"""
PDF Assembler
Convert markdown content and cover image to KDP-spec PDF
"""

from pathlib import Path
from typing import Callable, Optional

from fpdf import FPDF

from .config import BookConfig


class BookPDF(FPDF):
    """KDP interior PDF class"""
    
    def __init__(self, title: str = "", author: str = ""):
        super().__init__()
        self.book_title = title
        self.book_author = author
        self._past_title = False
    
    def header(self):
        """Page header"""
        if not self._past_title:
            return
        self.set_font("Helvetica", "", 8)
        # Use effective page width
        self.cell(self.epw, 5, self.book_title[:50], align="C")
        self.ln(8)
    
    def footer(self):
        """Page footer"""
        self.set_y(-15)
        self.set_font("Helvetica", "", 8)
        self.cell(self.epw, 10, str(self.page_no()), align="C")


class PDFAssembler:
    """PDF Assembler"""
    
    def __init__(self, progress_callback: Optional[Callable[[str], None]] = None):
        self.progress_callback = progress_callback or print
    
    def _log(self, message: str):
        """Progress output"""
        self.progress_callback(message)
    
    def build_interior(self, config: BookConfig, content: str, output_dir: Path) -> Path:
        """Generate interior PDF"""
        self._log("📄 Generating interior PDF...")
        
        pdf = BookPDF(title=config.title, author=config.author)
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.set_margins(20, 20, 20)
        
        # Title page
        pdf.add_page()
        pdf.ln(60)
        pdf.set_font("Helvetica", "B", 20)
        pdf.multi_cell(pdf.epw, 10, config.title, align="C")
        pdf.ln(15)
        pdf.set_font("Helvetica", "", 14)
        pdf.multi_cell(pdf.epw, 8, f"by {config.author}", align="C")
        
        pdf._past_title = True
        
        # Render content
        in_code_block = False
        for line in content.split("\n"):
            stripped = line.strip()
            
            # Handle code blocks - skip content inside
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                continue
            
            if in_code_block:
                continue
            
            if stripped.startswith("# "):
                continue  # Top-level title shown on title page
            
            elif stripped.startswith("## "):  # Chapter title
                pdf.add_page()
                pdf.ln(25)
                pdf.set_font("Helvetica", "B", 18)
                pdf.multi_cell(pdf.epw, 9, stripped[3:], align="C")
                pdf.ln(12)
                pdf.set_font("Helvetica", "", 11)
            
            elif stripped.startswith("### "):  # Subheading
                pdf.ln(4)
                pdf.set_font("Helvetica", "B", 13)
                pdf.multi_cell(pdf.epw, 6, stripped[4:])
                pdf.ln(2)
                pdf.set_font("Helvetica", "", 11)
            
            elif stripped.startswith("- ") or stripped.startswith("* "):  # List
                pdf.set_font("Helvetica", "", 11)
                pdf.multi_cell(pdf.epw, 5, f"  - {stripped[2:]}")
            
            elif stripped == "":  # Empty line
                pdf.ln(3)
            
            else:  # Body text
                pdf.set_font("Helvetica", "", 11)
                pdf.multi_cell(pdf.epw, 5, stripped)
        
        # Save
        output_dir.mkdir(parents=True, exist_ok=True)
        interior_path = output_dir / "interior.pdf"
        pdf.output(str(interior_path))
        
        self._log(f"✅ Interior PDF saved: {interior_path} ({pdf.page_no()} pages)")
        
        return interior_path
    
    def build_cover(self, cover_image_path: Path, output_dir: Path) -> Path:
        """Generate cover PDF"""
        self._log("📄 Generating cover PDF...")
        
        pdf = FPDF()
        pdf.add_page()
        pdf.image(str(cover_image_path), x=0, y=0, w=210, h=297)  # A4 mm
        
        output_dir.mkdir(parents=True, exist_ok=True)
        cover_pdf_path = output_dir / "cover.pdf"
        pdf.output(str(cover_pdf_path))
        
        self._log(f"✅ Cover PDF saved: {cover_pdf_path}")
        
        return cover_pdf_path
