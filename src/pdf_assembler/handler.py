"""
Lambda — PDF Assembler
─────────────────────────
콘텐츠 마크다운 + 표지 이미지를 KDP용 PDF 두 장(본문·표지)으로 조립합니다.

입력
  book_id        : 고유 책 식별자
  title          : 책 제목
  author         : 작가명
  content_s3_key : S3 경로 (마크다운)
  cover_s3_key   : S3 경로 (PNG)

출력
  pdf_s3_key       : 본문 PDF S3 경로
  cover_pdf_s3_key : 표지 PDF S3 경로
  interior_pages   : 본문 페이지 수

한국어 폰트
  Noto Sans KR .otf를 /tmp에 캐싱하여 사용합니다.
  빈 환경이면 폴백으로 Helvetica(영어만)로 렌더링됩니다.
"""

import os
import tempfile
import urllib.request

import boto3
from fpdf import FPDF

S3_BUCKET = os.environ["S3_BUCKET"]

# ── 폴트 경로 및 캐시 ─────────────────────────────────────────
FONT_NAME = "NotoKR"
FONT_URL  = "https://github.com/nicholasng1998/Noto-Sans-CJK-KR/raw/master/NotoSansCJKkr-Regular.otf"


def _font_path() -> str:
    return os.path.join(tempfile.gettempdir(), "NotoSansCJKkr-Regular.otf")


def _ensure_font() -> bool:
    """한국어 폰트 파일을 temp 디렉토리에 캐시하여 가져옴. 실패시 False 반환."""
    path = _font_path()
    if os.path.exists(path):
        return True
    try:
        urllib.request.urlretrieve(FONT_URL, path)
        return True
    except Exception:
        return False


# ── 커스턴 PDF 클래스 ─────────────────────────────────────────

class BookPDF(FPDF):
    """KDP 본문용 PDF — 헤더(제목)·푸터(페이지수)를 자동 렌더링."""

    def __init__(self, title: str = "", author: str = "", use_kr_font: bool = False):
        super().__init__()
        self.book_title   = title
        self.book_author  = author
        self._kr         = use_kr_font
        self._past_title = False          # 타이틀 페이지 이후에만 헤더 표시

        if self._kr:
            self.add_font(FONT_NAME, "", _font_path())

    # ── 폰트 설정 헬퍼 ──────────────────────────────────────────
    def _set(self, style: str = "", size: float = 12):
        if self._kr:
            self.set_font(FONT_NAME, "", size)   # OTF 단일 웨이트
        else:
            self.set_font("Helvetica", style, size)

    # ── FPDF 콜백 ───────────────────────────────────────────────
    def header(self):
        if not self._past_title:
            return
        self._set("", 8)
        self.cell(0, 5, self.book_title, align="C")
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self._set("", 8)
        self.cell(0, 10, str(self.page_no()), align="C")


# ── 핵심 로직 ─────────────────────────────────────────────────

def lambda_handler(event, context):
    book_id        = event["book_id"]
    title          = event["title"]
    author         = event["author"]
    content_s3_key = event["content_s3_key"]
    cover_s3_key   = event["cover_s3_key"]

    s3 = boto3.client("s3")

    # S3에서 콘텐츠와 표지 다운로드
    content_md = s3.get_object(Bucket=S3_BUCKET, Key=content_s3_key)["Body"].read().decode("utf-8")
    cover_bytes = s3.get_object(Bucket=S3_BUCKET, Key=cover_s3_key)["Body"].read()

    tmpdir         = tempfile.gettempdir()
    cover_img_path = os.path.join(tmpdir, "cover.png")
    with open(cover_img_path, "wb") as f:
        f.write(cover_bytes)

    use_kr = _ensure_font()

    # ── 본문 PDF ──────────────────────────────────────────────
    interior      = _build_interior(title, author, content_md, use_kr)
    interior_path = os.path.join(tmpdir, "interior.pdf")
    interior.output(interior_path)

    # ── 표지 PDF ──────────────────────────────────────────────
    cover_pdf      = _build_cover(cover_img_path)
    cover_pdf_path = os.path.join(tmpdir, "cover.pdf")
    cover_pdf.output(cover_pdf_path)

    # S3 업로드
    pdf_s3_key       = f"{book_id}/output/interior.pdf"
    cover_pdf_s3_key = f"{book_id}/output/cover.pdf"

    with open(interior_path, "rb") as f:
        s3.put_object(Bucket=S3_BUCKET, Key=pdf_s3_key, Body=f, ContentType="application/pdf")
    with open(cover_pdf_path, "rb") as f:
        s3.put_object(Bucket=S3_BUCKET, Key=cover_pdf_s3_key, Body=f, ContentType="application/pdf")

    return {
        "pdf_s3_key":       pdf_s3_key,
        "cover_pdf_s3_key": cover_pdf_s3_key,
        "interior_pages":   interior.page_no(),
    }


# ── PDF 빌더 ─────────────────────────────────────────────────

def _build_interior(title: str, author: str, content_md: str, use_kr: bool) -> BookPDF:
    pdf = BookPDF(title=title, author=author, use_kr_font=use_kr)
    pdf.set_auto_page_break(auto=True, margin=22)

    # ── 타이틀 페이지 ────────────────────────────────────────
    pdf.add_page()
    pdf.ln(65)
    pdf._set("B", 24)
    pdf.multi_cell(0, 11, title, align="C")
    pdf.ln(16)
    pdf._set("", 15)
    pdf.multi_cell(0, 9, f"by {author}", align="C")

    pdf._past_title = True   # 이후 페이지부터 헤더 활성화

    # ── 본문 렌더링 (간단한 Markdown → PDF) ────────────────
    for line in content_md.split("\n"):
        stripped = line.strip()

        if stripped.startswith("# "):
            continue                          # 최상위 제목은 타이틀 페이지에 이미 표시됨

        elif stripped.startswith("## "):      # ── 챕터 제목
            pdf.add_page()
            pdf.ln(28)
            pdf._set("B", 20)
            pdf.multi_cell(0, 10, stripped[3:], align="C")
            pdf.ln(14)
            pdf._set("", 11)

        elif stripped.startswith("### "):     # ── 소제목
            pdf.ln(5)
            pdf._set("B", 14)
            pdf.multi_cell(0, 7, stripped[4:])
            pdf.ln(2)
            pdf._set("", 11)

        elif stripped.startswith("- ") or stripped.startswith("* "):  # ── 리스트
            pdf._set("", 11)
            bullet = "-" if not pdf._kr else "\u2022"
            pdf.multi_cell(0, 5, f"    {bullet} {stripped[2:]}")

        elif stripped.startswith("**") and stripped.endswith("**"):   # ── 볼드 라인
            pdf._set("B", 11)
            pdf.multi_cell(0, 5, stripped.strip("*"))
            pdf._set("", 11)

        elif stripped == "":                  # ── 빈 줄
            pdf.ln(3)

        else:                                 # ── 본문
            pdf._set("", 11)
            pdf.multi_cell(0, 5, stripped)

    return pdf


def _build_cover(cover_image_path: str) -> FPDF:
    """표지 이미지를 A4 전체로 채우는 PDF."""
    pdf = FPDF()
    pdf.add_page()
    pdf.image(cover_image_path, x=0, y=0, w=210, h=297)  # A4 mm
    return pdf
