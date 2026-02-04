"""
Lambda — KDP Uploader
─────────────────────────
파이프라인의 마지막 단계로, 조립된 PDF를 검증하고 업로드 매니페스트를 생성합니다.

Amazon KDP는 공개 REST API를 제공하지 않습니다.
현재 구현은 MANIFEST_ONLY 모드로, 모든 파일과 메타데이터를 검증하고
S3에 매니페스트 JSON을 저장합니다.

향후 확장 옵션
  • UPLOAD_MODE=SP_API   → Amazon Selling Partner API를 통한 자동 업로드
  • UPLOAD_MODE=BROWSER  → Playwright를 사용한 KDP 웹 인터페이스 자동화

입력
  book_id, title, author, description, keywords, categories, price
  pdf_s3_key, cover_pdf_s3_key

출력
  status          : READY_FOR_UPLOAD | PUBLISHED
  asin            : PENDING (SP-API 미적용 시)
  manifest_s3_key : 매니페스트 파일 S3 경로
"""

import os
import json
from datetime import datetime, timezone

import boto3

S3_BUCKET    = os.environ["S3_BUCKET"]
UPLOAD_MODE  = os.environ.get("UPLOAD_MODE", "MANIFEST_ONLY")   # MANIFEST_ONLY | SP_API


def lambda_handler(event, context):
    book_id           = event["book_id"]
    title             = event["title"]
    author            = event["author"]
    pdf_s3_key        = event["pdf_s3_key"]
    cover_pdf_s3_key  = event["cover_pdf_s3_key"]

    s3 = boto3.client("s3")

    # ── 파일 존재 검증 ──────────────────────────────────────
    _validate_s3_object(s3, pdf_s3_key)
    _validate_s3_object(s3, cover_pdf_s3_key)

    # ── 매니페스트 구성 ─────────────────────────────────────
    manifest = {
        "book_id":  book_id,
        "title":    title,
        "author":   author,
        "files": {
            "interior_pdf": pdf_s3_key,
            "cover_pdf":    cover_pdf_s3_key,
        },
        "metadata": {
            "description": event.get("description", ""),
            "keywords":    event.get("keywords", []),
            "categories":  event.get("categories", []),
            "price_usd":   event.get("price", "9.99"),
            "language":    "ko",
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    # ── 업로드 모드별 처리 ──────────────────────────────────
    if UPLOAD_MODE == "SP_API":
        asin = _upload_via_sp_api(manifest)
        manifest["status"] = "PUBLISHED"
        manifest["asin"]   = asin
    else:
        manifest["status"] = "READY_FOR_UPLOAD"
        manifest["asin"]   = "PENDING"

    # 매니페스트 S3 저장
    manifest_s3_key = f"{book_id}/output/manifest.json"
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=manifest_s3_key,
        Body=json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"),
        ContentType="application/json",
    )

    return {
        "status":          manifest["status"],
        "asin":            manifest["asin"],
        "manifest_s3_key": manifest_s3_key,
    }


# ── 검증 ──────────────────────────────────────────────────────

def _validate_s3_object(s3_client, key: str):
    """S3 객체가 존재하는지 확인. 없으면 예외 발생."""
    try:
        s3_client.head_object(Bucket=S3_BUCKET, Key=key)
    except Exception as exc:
        raise ValueError(f"S3 객체를 찾을 수 없습니다: s3://{S3_BUCKET}/{key}") from exc


# ── SP-API 플레이스홀더 ───────────────────────────────────────

def _upload_via_sp_api(manifest: dict) -> str:
    """
    Amazon Selling Partner API를 통한 KDP 업로드.

    사전 조건:
      1. Amazon Developer Portal에서 SP-API 앱 등록
      2. LWA (Login with Amazon) 클라이언트 ID·Secret 획득
      3. Secrets Manager의 'kdp/credentials'에 저장

    TODO: SP-API 클라이언트 구현 후 활성화
    """
    raise NotImplementedError(
        "SP-API 모듈이 아직 구현되지 않았습니다. "
        "UPLOAD_MODE=MANIFEST_ONLY로 사용하거나, SP-API 클라이언트를 구현하세요."
    )
