#!/usr/bin/env python3
"""
KDP 파이프라인 수동 실행 스크립트
──────────────────────────────────
사용법
  python scripts/start_pipeline.py                          # 기본 설정 파일 사용
  python scripts/start_pipeline.py --config path/to/cfg.yaml
  python scripts/start_pipeline.py --dry-run                # 실행 안 하고 입력값만 출력
  python scripts/start_pipeline.py --region us-east-1       # AWS 리전 지정
"""

import argparse
import json
import uuid
import sys

import yaml
import boto3


def _load_config(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _build_input(config: dict) -> dict:
    book = config["book"]
    meta = book.get("metadata", {})
    return {
        "book_id":      book.get("id") or str(uuid.uuid4()),
        "title":        book["title"],
        "author":       book["author"],
        "topic":        book["topic"],
        "genre":        book.get("genre", "General"),
        "style":        book.get("cover", {}).get("style", "modern minimalist"),
        "language":     book.get("language", "ko"),
        "outline":      book.get("outline", ""),
        "description":  meta.get("description", ""),
        "keywords":     meta.get("keywords", []),
        "categories":   meta.get("categories", []),
        "price":        meta.get("price", "9.99"),
    }


def _find_state_machine_arn(sfn_client, name_fragment: str) -> str | None:
    """파이프라인 State Machine ARN을 이름으로 검색."""
    paginator = sfn_client.get_paginator("list_state_machines")
    for page in paginator.paginate():
        for sm in page["stateMachines"]:
            if name_fragment in sm["name"]:
                return sm["stateMachineArn"]
    return None


def main():
    parser = argparse.ArgumentParser(description="KDP 파이프라인 실행")
    parser.add_argument("--config",   default="config/book_config.yaml")
    parser.add_argument("--region",   default="ap-northeast-2")
    parser.add_argument("--dry-run",  action="store_true", help="실행하지 않고 입력값만 출력")
    args = parser.parse_args()

    config       = _load_config(args.config)
    pipeline_in  = _build_input(config)

    if args.dry_run:
        print(json.dumps(pipeline_in, ensure_ascii=False, indent=2))
        return

    # ── Step Functions 실행 ──────────────────────────────────
    sfn = boto3.client("stepfunctions", region_name=args.region)
    sm_arn = _find_state_machine_arn(sfn, "kdp-publishing-pipeline")

    if not sm_arn:
        print("[ERROR] 'kdp-publishing-pipeline' State Machine을 찾을 수 없습니다.")
        print("        먼저 'make deploy'로 인프라를 배포하세요.")
        sys.exit(1)

    execution = sfn.start_execution(
        stateMachineArn=sm_arn,
        name=f"kdp-{pipeline_in['book_id']}-{uuid.uuid4().hex[:8]}",
        input=json.dumps(pipeline_in, ensure_ascii=False),
    )

    print("파이프라인 시작!")
    print(f"  Execution ARN : {execution['executionArn']}")
    print(f"  Book ID       : {pipeline_in['book_id']}")
    print(f"  Title         : {pipeline_in['title']}")
    print(f"\nAWS Console에서 실행 상태를 확인할 수 있습니다.")


if __name__ == "__main__":
    main()
