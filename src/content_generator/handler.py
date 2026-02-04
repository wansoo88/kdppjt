"""
Lambda — Content Generator
───────────────────────────
GPT-4o를 사용하여 책 콘텐츠를 자동 생성합니다.

입력 (Step Functions Payload)
  book_id   : 고유 책 식별자
  title     : 책 제목
  topic     : 주제
  outline   : 목차 (빈 문자열이면 AI가 자동 생성)
  language  : 작성 언어 (기본 "ko")

출력
  content_s3_key : S3에 저장된 마크다운 파일 경로
  word_count     : 생성된 단어 수
"""

import os
import boto3
from openai import OpenAI

S3_BUCKET = os.environ["S3_BUCKET"]
OPENAI_SECRET_ARN = os.environ["OPENAI_SECRET_ARN"]


# ── Secrets Manager 캐시 ──────────────────────────────────────
_api_key_cache = None


def _get_openai_key() -> str:
    global _api_key_cache
    if _api_key_cache is None:
        client = boto3.client("secretsmanager")
        _api_key_cache = client.get_secret_value(SecretId=OPENAI_SECRET_ARN)["SecretString"]
    return _api_key_cache


# ── 핵심 로직 ─────────────────────────────────────────────────

def lambda_handler(event, context):
    book_id  = event["book_id"]
    title    = event["title"]
    topic    = event["topic"]
    outline  = event.get("outline", "")
    language = event.get("language", "ko")

    client = OpenAI(api_key=_get_openai_key())

    # outline이 비어있으면 AI로 생성
    if not outline or outline.strip() == "":
        outline = _generate_outline(client, title, topic, language)

    chapters = _parse_chapters(outline)
    content  = _generate_full_book(client, title, topic, chapters, language)

    # S3 저장
    s3_key = f"{book_id}/content/manuscript.md"
    boto3.client("s3").put_object(
        Bucket=S3_BUCKET,
        Key=s3_key,
        Body=content.encode("utf-8"),
        ContentType="text/markdown",
    )

    return {
        "content_s3_key": s3_key,
        "word_count": len(content.split()),
    }


# ── OpenAI 호출 헬퍼 ─────────────────────────────────────────

def _generate_outline(client: OpenAI, title: str, topic: str, language: str) -> str:
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": f"You are a professional book outliner. Always respond in {language}."},
            {"role": "user",   "content": (
                f"다음 책의 상세 목차를 작성해주세요.\n"
                f"제목: {title}\n"
                f"주제: {topic}\n\n"
                f"12~15개 챕터를 작성하고, 각 챕터에 세부 소제목 2~3개를 포함시켜주세요.\n"
                f"형식: '1. 챕터 제목'"
            )},
        ],
        max_tokens=1500,
    )
    return resp.choices[0].message.content


def _parse_chapters(outline: str) -> list[str]:
    """목차 텍스트에서 챕터 제목 리스트 추출."""
    chapters = []
    for line in outline.split("\n"):
        line = line.strip()
        if not line:
            continue
        # "1. 제목", "Chapter 1", "챕터 1" 등 다양한 패턴 매칭
        for i in range(1, 25):
            if line.startswith(f"{i}.") or line.startswith(f"{i})"):
                chapters.append(line.lstrip("0123456789.)# ").strip())
                break
    return chapters if chapters else ["개론", "본론", "결론"]


def _generate_full_book(client: OpenAI, title: str, topic: str, chapters: list[str], language: str) -> str:
    """챕터별로 콘텐츠를 생성하여 마크다운으로 조립."""
    lines = [f"# {title}\n"]

    for idx, chapter_title in enumerate(chapters, 1):
        chapter_md = _generate_chapter(client, title, topic, chapter_title, idx, language)
        lines.append(chapter_md)

    return "\n\n".join(lines)


def _generate_chapter(client: OpenAI, title: str, topic: str, chapter_title: str, num: int, language: str) -> str:
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    f"You are a professional author writing a book in {language}. "
                    f"Write detailed, engaging, and informative chapters with clear structure."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"책 제목: {title}\n"
                    f"전체 주제: {topic}\n"
                    f"현재 챕터: Chapter {num} — {chapter_title}\n\n"
                    f"이 챕터를 1500~2000자 정도로 작성해주세요.\n"
                    f"### 소제목을 3개 이상 사용하여 구조를 잡고, 실제 사례와 설명을 포함시켜주세요."
                ),
            },
        ],
        max_tokens=3000,
    )
    body = resp.choices[0].message.content
    return f"## Chapter {num}: {chapter_title}\n\n{body}"
