"""
Unit tests — cover_designer/handler.py
"""

import os
import importlib.util
from unittest.mock import MagicMock

import pytest

_HANDLER_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "src", "cover_designer", "handler.py")
)


@pytest.fixture()
def handler(monkeypatch):
    monkeypatch.setenv("S3_BUCKET",         "test-bucket")
    monkeypatch.setenv("OPENAI_SECRET_ARN", "arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:test")

    spec = importlib.util.spec_from_file_location("_cd_handler", _HANDLER_FILE)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod._api_key_cache = None
    return mod


def _setup_mocks(handler, monkeypatch):
    """boto3 · OpenAI · requests 공통 모킹."""
    sm = MagicMock()
    sm.get_secret_value.return_value = {"SecretString": "sk-test"}
    s3 = MagicMock()

    mock_boto3 = MagicMock()
    mock_boto3.client = lambda svc, **kw: sm if svc == "secretsmanager" else s3
    monkeypatch.setattr(handler, "boto3", mock_boto3)

    img_resp = MagicMock()
    img_resp.data = [MagicMock(url="https://example.com/img.png")]
    client = MagicMock()
    client.images.generate.return_value = img_resp
    monkeypatch.setattr(handler, "OpenAI", MagicMock(return_value=client))

    mock_requests = MagicMock()
    mock_requests.get.return_value = MagicMock(content=b"\x89PNG-fake-bytes")
    monkeypatch.setattr(handler, "requests", mock_requests)

    return client, s3


class TestCoverDesigner:
    def test_returns_cover_s3_key(self, handler, monkeypatch):
        client, s3 = _setup_mocks(handler, monkeypatch)

        result = handler.lambda_handler({
            "book_id": "book-cover-01",
            "title":   "커버 테스트",
            "genre":   "technology",
            "style":   "dark futuristic",
        }, None)

        assert result["cover_s3_key"] == "book-cover-01/cover/cover.png"
        client.images.generate.assert_called_once()
        s3.put_object.assert_called_once()

    def test_dall_e_params(self, handler, monkeypatch):
        client, _ = _setup_mocks(handler, monkeypatch)

        handler.lambda_handler({"book_id": "x", "title": "T", "genre": "fiction", "style": "s"}, None)

        kw = client.images.generate.call_args[1]
        assert kw["model"]   == "dall-e-3"
        assert kw["size"]    == "1024x1024"
        assert kw["quality"] == "hd"

    def test_prompt_contains_genre_template(self, handler):
        prompt = handler._build_prompt("제목", "technology", "minimalist")
        assert "futuristic" in prompt
        assert "제목" in prompt

    def test_prompt_fallback_for_unknown_genre(self, handler):
        prompt = handler._build_prompt("제목", "unknown_genre", "style")
        assert "제목" in prompt
        assert "professional" in prompt.lower()
