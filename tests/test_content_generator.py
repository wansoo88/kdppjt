"""
Unit tests — content_generator/handler.py

모듈 이름이 모두 handler.py이므로 importlib.util을 사용하여
각 테스트 파일마다 독립적으로 로드합니다.
"""

import os
import importlib.util
from unittest.mock import MagicMock

import pytest

_HANDLER_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "src", "content_generator", "handler.py")
)


@pytest.fixture()
def handler(monkeypatch):
    """content_generator 핸들러를 깨끗하게 로드."""
    monkeypatch.setenv("S3_BUCKET",          "test-bucket")
    monkeypatch.setenv("OPENAI_SECRET_ARN",  "arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:test")

    spec = importlib.util.spec_from_file_location("_cg_handler", _HANDLER_FILE)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod._api_key_cache = None   # 캐시 초기화
    return mod


def _setup_mocks(handler, monkeypatch, api_reply: str):
    """boto3 + OpenAI 공통 모킹."""
    sm = MagicMock()
    sm.get_secret_value.return_value = {"SecretString": "sk-test-key"}
    s3 = MagicMock()

    mock_boto3 = MagicMock()
    mock_boto3.client = lambda svc, **kw: sm if svc == "secretsmanager" else s3
    monkeypatch.setattr(handler, "boto3", mock_boto3)

    resp = MagicMock()
    resp.choices = [MagicMock()]
    resp.choices[0].message.content = api_reply
    client = MagicMock()
    client.chat.completions.create.return_value = resp
    monkeypatch.setattr(handler, "OpenAI", MagicMock(return_value=client))

    return s3, client


class TestContentGenerator:
    def test_returns_s3_key_and_word_count(self, handler, monkeypatch):
        s3, _ = _setup_mocks(handler, monkeypatch, "챕터 본문입니다. 여러 단어가 포함되어 있습니다.")

        result = handler.lambda_handler({
            "book_id":  "book-test-01",
            "title":    "테스트 책",
            "topic":    "테스트 주제",
            "outline":  "1. 개론\n2. 본론\n3. 결론",
            "language": "ko",
        }, None)

        assert result["content_s3_key"] == "book-test-01/content/manuscript.md"
        assert result["word_count"] > 0
        s3.put_object.assert_called_once()

    def test_generates_outline_when_empty(self, handler, monkeypatch):
        _, client = _setup_mocks(handler, monkeypatch, "1. 챕터 하나\n2. 챕터 둘\n3. 챕터 셋")

        handler.lambda_handler({
            "book_id":  "book-test-02",
            "title":    "빈 목차 책",
            "topic":    "주제",
            "outline":  "",            # 빈 값 → AI 자동 생성
            "language": "ko",
        }, None)

        # outline 생성 1회 + 챕터 3개 생성 = 최소 4회 호출
        assert client.chat.completions.create.call_count >= 4

    def test_parse_chapters_extracts_correctly(self, handler):
        chapters = handler._parse_chapters("1. 첫 챕터\n2. 두번째\n\n3. 세번째\n")
        assert len(chapters) == 3
        assert chapters[0] == "첫 챕터"

    def test_parse_chapters_fallback(self, handler):
        assert handler._parse_chapters("") == ["개론", "본론", "결론"]
