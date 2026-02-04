"""
Unit tests — kdp_uploader/handler.py
"""

import json
import os
import importlib.util
from unittest.mock import MagicMock

import pytest

_HANDLER_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "src", "kdp_uploader", "handler.py")
)

SAMPLE_EVENT = {
    "book_id":          "up-01",
    "title":            "업로드 테스트 책",
    "author":           "테스트 작가",
    "description":      "테스트 설명",
    "keywords":         ["테스트", "AWS"],
    "categories":       ["Technology"],
    "price":            "19.99",
    "pdf_s3_key":       "up-01/output/interior.pdf",
    "cover_pdf_s3_key": "up-01/output/cover.pdf",
}


def _load_handler(monkeypatch, upload_mode: str = "MANIFEST_ONLY"):
    """환경 변수를 세팅한 후 핸들러를 로드."""
    monkeypatch.setenv("S3_BUCKET",      "test-bucket")
    monkeypatch.setenv("UPLOAD_MODE",    upload_mode)
    monkeypatch.setenv("KDP_SECRET_ARN", "arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:test")

    spec = importlib.util.spec_from_file_location("_ku_handler", _HANDLER_FILE)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _mock_s3(handler, monkeypatch, head_ok: bool = True):
    s3 = MagicMock()
    if not head_ok:
        s3.head_object.side_effect = Exception("404 Not Found")

    mock_boto3 = MagicMock()
    mock_boto3.client.return_value = s3
    monkeypatch.setattr(handler, "boto3", mock_boto3)
    return s3


class TestKdpUploader:
    def test_manifest_created_successfully(self, monkeypatch):
        handler = _load_handler(monkeypatch, "MANIFEST_ONLY")
        s3      = _mock_s3(handler, monkeypatch)

        result = handler.lambda_handler(SAMPLE_EVENT, None)

        assert result["status"]          == "READY_FOR_UPLOAD"
        assert result["asin"]            == "PENDING"
        assert result["manifest_s3_key"] == "up-01/output/manifest.json"

        # put_object 호출 내용으로 매니페스트 검증
        put_kw   = s3.put_object.call_args[1]
        manifest = json.loads(put_kw["Body"].decode("utf-8"))
        assert manifest["title"]                  == "업로드 테스트 책"
        assert manifest["files"]["interior_pdf"]  == "up-01/output/interior.pdf"
        assert manifest["metadata"]["price_usd"]  == "19.99"

    def test_raises_when_s3_object_missing(self, monkeypatch):
        handler = _load_handler(monkeypatch, "MANIFEST_ONLY")
        _mock_s3(handler, monkeypatch, head_ok=False)

        with pytest.raises(ValueError, match="S3 객체를 찾을 수 없습니다"):
            handler.lambda_handler(SAMPLE_EVENT, None)

    def test_sp_api_mode_raises_not_implemented(self, monkeypatch):
        handler = _load_handler(monkeypatch, "SP_API")    # SP_API 모드로 로드
        _mock_s3(handler, monkeypatch)

        with pytest.raises(NotImplementedError):
            handler.lambda_handler(SAMPLE_EVENT, None)
