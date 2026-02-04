"""
KDP 자동화 파이프라인 — CDK Stack

아키텍처 개요
─────────────
                ┌─────────────────── Step Functions ───────────────────┐
                │                                                       │
  EventBridge   │   ┌──────────────┐   ┌──────────────┐               │
  (스케줄/수동) ──►  │ ContentGen   │   │ CoverDesign  │  ← 병렬 실행  │
                │   │ (GPT-4o)     │   │ (DALL-E 3)   │               │
                │   └──────┬───────┘   └──────┬───────┘               │
                │          └────────┬─────────┘                        │
                │                   ▼                                   │
                │          ┌────────────────┐                          │
                │          │  PDF Assembler │  ← 내부 + 표지 PDF       │
                │          └───────┬────────┘                          │
                │                  ▼                                    │
                │          ┌────────────────┐                          │
                │          │  KDP Uploader  │  ← 매니페스트 생성/SP-API│
                │          └───────┬────────┘                          │
                └──────────────────┼───────────────────────────────────┘
                                   ▼
                            SNS → 알림 (성공/실패)

AWS 리소스
──────────
  S3              — 콘텐츠·표지·PDF 아티팩트 저장
  Lambda ×4       — ContentGen / CoverDesign / PdfAssembler / KdpUploader
  Step Functions  — 파이프라인 오케스트레이션 (Parallel + Catch)
  SNS             — 성공·실패 알림
  Secrets Manager — OpenAI API Key, KDP 자격증명
"""

import os
from aws_cdk import (
    Stack,
    Duration,
    BundlingOptions,
    RemovalPolicy,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    aws_sns as sns,
    aws_secretsmanager as secretsmanager,
    aws_logs as logs,
)
from constructs import Construct

# 프로젝트 루트 (infrastructure/ 한 단계 위)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class KdpPipelineStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ── S3: 아티팩트 저장소 ──────────────────────────────────────
        assets_bucket = s3.Bucket(
            self,
            "AssetsBucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            versioned=True,
        )

        # ── Secrets Manager ──────────────────────────────────────────
        openai_secret = secretsmanager.Secret(
            self,
            "OpenAISecret",
            secret_name="kdp/openai-api-key",
            description="OpenAI API Key (GPT-4o + DALL-E 3)",
        )
        kdp_secret = secretsmanager.Secret(
            self,
            "KDPSecret",
            secret_name="kdp/credentials",
            description="KDP / Amazon SP-API 자격증명",
        )

        # ── SNS: 성공·실패 알림 ──────────────────────────────────────
        notification_topic = sns.Topic(
            self,
            "NotificationTopic",
            topic_name="kdp-pipeline-notifications",
        )

        # ── Lambda 생성 헬퍼 ─────────────────────────────────────────
        def make_lambda(
            id: str,
            src_dir: str,
            env: dict,
            timeout_min: int = 1,
            memory_mb: int = 256,
        ) -> _lambda.Function:
            return _lambda.Function(
                self,
                id,
                runtime=_lambda.Runtime.PYTHON_3_12,
                handler="handler.lambda_handler",
                code=_lambda.Code.from_asset(
                    path=os.path.join(PROJECT_ROOT, "src", src_dir),
                    bundling=BundlingOptions(
                        image=_lambda.Runtime.PYTHON_3_12.bundling_image,
                        command=[
                            "bash", "-c",
                            "pip install -t /asset-output -r requirements.txt "
                            "&& cp -au /asset-input/. /asset-output",
                        ],
                    ),
                ),
                environment=env,
                timeout=Duration.minutes(timeout_min),
                memory_size=memory_mb,
                log_retention=logs.RetentionDays.ONE_WEEK,
            )

        # ── Lambda ×4 ────────────────────────────────────────────────
        common_env = {
            "S3_BUCKET": assets_bucket.bucket_name,
            "OPENAI_SECRET_ARN": openai_secret.secret_arn,
        }

        content_fn = make_lambda("ContentGenerator", "content_generator", common_env, timeout_min=5, memory_mb=512)
        cover_fn   = make_lambda("CoverDesigner",    "cover_designer",    common_env, timeout_min=3, memory_mb=512)
        pdf_fn     = make_lambda("PdfAssembler",     "pdf_assembler",     common_env, timeout_min=5, memory_mb=1024)
        upload_fn  = make_lambda(
            "KdpUploader", "kdp_uploader",
            {**common_env, "KDP_SECRET_ARN": kdp_secret.secret_arn, "UPLOAD_MODE": "MANIFEST_ONLY"},
            timeout_min=10, memory_mb=512,
        )

        # ── IAM 권한 ─────────────────────────────────────────────────
        assets_bucket.grant_read_write(content_fn)
        assets_bucket.grant_read_write(cover_fn)
        assets_bucket.grant_read_write(pdf_fn)
        assets_bucket.grant_read(upload_fn)

        openai_secret.grant_read(content_fn)
        openai_secret.grant_read(cover_fn)
        kdp_secret.grant_read(upload_fn)

        # ── Step Functions 상태 정의 ──────────────────────────────────

        # — 실패 알림 (종료 상태) —
        notify_failure = tasks.SnsPublish(
            self, "NotifyFailure",
            topic=notification_topic,
            message=sfn.TaskInput.from_object({
                "pipeline": "kdp-publishing-pipeline",
                "status": "FAILED",
                "note": "Step Functions 콘솔에서 실행 로그를 확인하세요.",
            }),
        )

        # — 성공 알림 (종료 상태) —
        notify_success = tasks.SnsPublish(
            self, "NotifySuccess",
            topic=notification_topic,
            message=sfn.TaskInput.from_object({
                "pipeline": "kdp-publishing-pipeline",
                "status": "PUBLISHED",
                "book_id": sfn.JsonPath.string_at("$.book_id"),
                "title":   sfn.JsonPath.string_at("$.title"),
                "asin":    sfn.JsonPath.string_at("$.upload_result.asin"),
            }),
        )

        # — Task: 콘텐츠 생성 —
        generate_content = tasks.LambdaInvoke(
            self, "GenerateContent",
            lambda_function=content_fn,
            payload=sfn.TaskInput.from_object({
                "book_id":  sfn.JsonPath.string_at("$.book_id"),
                "title":    sfn.JsonPath.string_at("$.title"),
                "topic":    sfn.JsonPath.string_at("$.topic"),
                "outline":  sfn.JsonPath.string_at("$.outline"),
                "language": sfn.JsonPath.string_at("$.language"),
            }),
            result_selector={
                "content_s3_key": sfn.JsonPath.string_at("$.Payload.content_s3_key"),
                "word_count":     sfn.JsonPath.number_at("$.Payload.word_count"),
            },
        )
        generate_content.add_retry(sfn.Retry(errors=["Lambda.ServiceException"], max_attempts=2))

        # — Task: 표지 생성 —
        generate_cover = tasks.LambdaInvoke(
            self, "GenerateCover",
            lambda_function=cover_fn,
            payload=sfn.TaskInput.from_object({
                "book_id": sfn.JsonPath.string_at("$.book_id"),
                "title":   sfn.JsonPath.string_at("$.title"),
                "genre":   sfn.JsonPath.string_at("$.genre"),
                "style":   sfn.JsonPath.string_at("$.style"),
            }),
            result_selector={
                "cover_s3_key": sfn.JsonPath.string_at("$.Payload.cover_s3_key"),
            },
        )
        generate_cover.add_retry(sfn.Retry(errors=["Lambda.ServiceException"], max_attempts=2))

        # — Parallel: 콘텐츠 + 표지 동시 생성 —
        parallel = sfn.Parallel(
            self, "ParallelGeneration",
            result_path="$.parallel_result",
        )
        parallel.add_branch(generate_content)
        parallel.add_branch(generate_cover)
        parallel.add_catch(sfn.CatchProps(errors=["States.ALL"], result_path="$.error", next_state=notify_failure))

        # — Task: PDF 조립 —
        assemble_pdf = tasks.LambdaInvoke(
            self, "AssemblePDF",
            lambda_function=pdf_fn,
            payload=sfn.TaskInput.from_object({
                "book_id":        sfn.JsonPath.string_at("$.book_id"),
                "title":          sfn.JsonPath.string_at("$.title"),
                "author":         sfn.JsonPath.string_at("$.author"),
                "content_s3_key": sfn.JsonPath.string_at("$.parallel_result[0].content_s3_key"),
                "cover_s3_key":   sfn.JsonPath.string_at("$.parallel_result[1].cover_s3_key"),
            }),
            result_path="$.assembly_result",
            result_selector={
                "pdf_s3_key":       sfn.JsonPath.string_at("$.Payload.pdf_s3_key"),
                "cover_pdf_s3_key": sfn.JsonPath.string_at("$.Payload.cover_pdf_s3_key"),
            },
        )
        assemble_pdf.add_catch(sfn.CatchProps(errors=["States.ALL"], result_path="$.error", next_state=notify_failure))

        # — Task: KDP 업로드 —
        kdp_upload = tasks.LambdaInvoke(
            self, "UploadToKDP",
            lambda_function=upload_fn,
            payload=sfn.TaskInput.from_object({
                "book_id":         sfn.JsonPath.string_at("$.book_id"),
                "title":           sfn.JsonPath.string_at("$.title"),
                "author":          sfn.JsonPath.string_at("$.author"),
                "description":     sfn.JsonPath.string_at("$.description"),
                "keywords":        sfn.JsonPath.string_at("$.keywords"),
                "categories":      sfn.JsonPath.string_at("$.categories"),
                "price":           sfn.JsonPath.string_at("$.price"),
                "pdf_s3_key":      sfn.JsonPath.string_at("$.assembly_result.pdf_s3_key"),
                "cover_pdf_s3_key":sfn.JsonPath.string_at("$.assembly_result.cover_pdf_s3_key"),
            }),
            result_path="$.upload_result",
            result_selector={
                "status":          sfn.JsonPath.string_at("$.Payload.status"),
                "asin":            sfn.JsonPath.string_at("$.Payload.asin"),
                "manifest_s3_key": sfn.JsonPath.string_at("$.Payload.manifest_s3_key"),
            },
        )
        kdp_upload.add_catch(sfn.CatchProps(errors=["States.ALL"], result_path="$.error", next_state=notify_failure))

        # ── 상태 연결: Parallel → PDF → Upload → 성공 알림 ────────────
        parallel.next(assemble_pdf)
        assemble_pdf.next(kdp_upload)
        kdp_upload.next(notify_success)

        # ── State Machine ────────────────────────────────────────────
        sfn.StateMachine(
            self,
            "KdpPipeline",
            state_machine_name="kdp-publishing-pipeline",
            definition_body=sfn.DefinitionBody.from_chainable(parallel),
            timeout=Duration.hours(1),
            log_configuration=sfn.LogConfiguration(
                destinations=[logs.LogGroup(self, "PipelineLogGroup")],
                level=sfn.LogLevel.ALL,
            ),
        )
