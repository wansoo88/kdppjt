"""
Unit tests — pdf_assembler/handler.py
"""

import io
import os
import importlib.util
from unittest.mock import MagicMock

import pytest
from PIL import Image

_HANDLER_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "src", "pdf_assembler", "handler.py")
)

SAMPLE_MD = """\
# Assembly Test Book

## Chapter 1: Introduction

### Background
This is the introduction chapter with multiple lines of text for testing.

- Point one here
- Point two here

### Key Points
Moving into the main body now.

## Chapter 2: Conclusion

This is the closing chapter of the test book.
"""


def _make_png_bytes() -> bytes:
    """유효한 100×100 테스트 PNG 생성."""
    buf = io.BytesIO()
    Image.new("RGB", (100, 100), color=(80, 120, 200)).save(buf, format="PNG")
    return buf.getvalue()


TEST_PNG = _make_png_bytes()


@pytest.fixture()
def handler(monkeypatch):
    monkeypatch.setenv("S3_BUCKET", "test-bucket")

    spec = importlib.util.spec_from_file_location("_pa_handler", _HANDLER_FILE)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _setup_mocks(handler, monkeypatch):
    """boto3 + _ensure_font 모킹."""
    monkeypatch.setattr(handler, "_ensure_font", lambda: False)   # Korean font 건너뜀

    s3 = MagicMock()
    s3.get_object.side_effect = lambda Bucket, Key: {
        "Body": MagicMock(read=lambda: SAMPLE_MD.encode("utf-8"))
    } if "content" in Key else {
        "Body": MagicMock(read=lambda: TEST_PNG)
    }

    mock_boto3 = MagicMock()
    mock_boto3.client.return_value = s3
    monkeypatch.setattr(handler, "boto3", mock_boto3)
    return s3


class TestPdfAssembler:
    def test_produces_two_pdfs(self, handler, monkeypatch):
        s3 = _setup_mocks(handler, monkeypatch)

        result = handler.lambda_handler({
            "book_id":        "asm-01",
            "title":          "PDF Assembly Test",
            "author":         "Test Author",
            "content_s3_key": "asm-01/content/manuscript.md",
            "cover_s3_key":   "asm-01/cover/cover.png",
        }, None)

        assert result["pdf_s3_key"]       == "asm-01/output/interior.pdf"
        assert result["cover_pdf_s3_key"] == "asm-01/output/cover.pdf"
        assert result["interior_pages"]   >= 2      # 타이틀 + 챕터 최소 2
        assert s3.put_object.call_count   == 2

    def test_interior_pages_count(self, handler, monkeypatch):
        _setup_mocks(handler, monkeypatch)

        result = handler.lambda_handler({
            "book_id":        "asm-02",
            "title":          "Page Count Test",
            "author":         "Author",
            "content_s3_key": "asm-02/content/manuscript.md",
            "cover_s3_key":   "asm-02/cover/cover.png",
        }, None)

        # 타이틀 1 + 챕터 2 = 최소 3 페이지
        assert result["interior_pages"] >= 3
