"""
Lambda — Cover Designer
─────────────────────────
DALL-E 3를 사용하여 책 표지 이미지를 생성합니다.

입력
  book_id : 고유 책 식별자
  title   : 책 제목
  genre   : 장르 (technology | business | fiction | self-help | science)
  style   : 디자인 스타일 (예: "modern minimalist")

출력
  cover_s3_key : S3에 저장된 표지 PNG 경로
"""

import os
import requests
import boto3
from openai import OpenAI

S3_BUCKET = os.environ["S3_BUCKET"]
OPENAI_SECRET_ARN = os.environ["OPENAI_SECRET_ARN"]

_api_key_cache = None


def _get_openai_key() -> str:
    global _api_key_cache
    if _api_key_cache is None:
        client = boto3.client("secretsmanager")
        _api_key_cache = client.get_secret_value(SecretId=OPENAI_SECRET_ARN)["SecretString"]
    return _api_key_cache


# ── 장르별 프롬프트 템플릿 ─────────────────────────────────────

GENRE_PROMPTS = {
    "technology": (
        "A {style} book cover for a technology book. "
        "Clean, futuristic design with subtle digital circuit patterns and cool-toned gradients. "
    ),
    "business": (
        "A {style} book cover for a business book. "
        "Sophisticated, corporate feel with geometric shapes and warm gold or navy tones. "
    ),
    "fiction": (
        "A {style} book cover for a fiction novel. "
        "Dramatic, cinematic composition with moody lighting and rich colours. "
    ),
    "self-help": (
        "A {style} book cover for a self-help and motivation book. "
        "Bright, inspiring design with sunrise or nature imagery and uplifting energy. "
    ),
    "science": (
        "A {style} book cover for a science book. "
        "Visually striking design with macro-photography style scientific imagery. "
    ),
}

DEFAULT_TEMPLATE = (
    "A {style} professional book cover. "
    "Clean, modern design suitable for Amazon KDP publishing. "
)


def _build_prompt(title: str, genre: str, style: str) -> str:
    template = GENRE_PROMPTS.get(genre.lower(), DEFAULT_TEMPLATE)
    base = template.format(style=style)
    # 제목을 프롬프트에 포함 (DALL-E 텍스트 렌더링은 불안정하여 최선의 시도)
    return (
        f"{base}"
        f"The words '{title}' should appear prominently on the cover in a clean readable font. "
        f"Professional publishing quality, high resolution, no watermarks."
    )


# ── 핵심 로직 ─────────────────────────────────────────────────

def lambda_handler(event, context):
    book_id = event["book_id"]
    title   = event["title"]
    genre   = event.get("genre", "General")
    style   = event.get("style", "modern minimalist")

    client = OpenAI(api_key=_get_openai_key())
    prompt = _build_prompt(title, genre, style)

    # DALL-E 3 이미지 생성
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="hd",
        style="natural",
        n=1,
    )
    image_url = response.data[0].url

    # URL에서 이미지 바이트 다운로드
    img_bytes = requests.get(image_url, timeout=30).content

    # S3 저장
    s3_key = f"{book_id}/cover/cover.png"
    boto3.client("s3").put_object(
        Bucket=S3_BUCKET,
        Key=s3_key,
        Body=img_bytes,
        ContentType="image/png",
    )

    return {"cover_s3_key": s3_key}
