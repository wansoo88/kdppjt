#!/usr/bin/env python3
"""
KDP Book Merger
Merge manually uploaded manuscript and cover into KDP-ready PDF

Usage:
    python merge.py --book books/my-book
    python merge.py --book books/my-book --output output/my-book
"""

import argparse
import sys
from pathlib import Path

from kdp.pdf_assembler import PDFAssembler
from kdp.quality_checker import QualityChecker


def load_book_config(book_dir: Path) -> dict:
    """Load book config or use defaults"""
    config_path = book_dir / "config.yaml"
    
    defaults = {
        "title": book_dir.name.replace("-", " ").title(),
        "author": "Unknown Author",
        "metadata": {
            "description": "",
            "keywords": [],
            "categories": [],
            "price": "9.99"
        }
    }
    
    if config_path.exists():
        import yaml
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if data and "book" in data:
                book_data = data["book"]
                defaults["title"] = book_data.get("title", defaults["title"])
                defaults["author"] = book_data.get("author", defaults["author"])
                if "metadata" in book_data:
                    defaults["metadata"].update(book_data["metadata"])
    
    return defaults


class SimpleConfig:
    """Simple config object for PDFAssembler"""
    def __init__(self, title: str, author: str):
        self.title = title
        self.author = author


def main():
    parser = argparse.ArgumentParser(
        description="Merge manuscript and cover into KDP-ready PDF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
    python merge.py --book books/my-book
    
Book folder structure:
    books/my-book/
        manuscript.md    <- Your content (required)
        cover.png        <- Your cover image (required)  
        config.yaml      <- Book metadata (optional)
        """
    )
    
    parser.add_argument(
        "--book", "-b",
        required=True,
        help="Path to book folder containing manuscript.md and cover.png"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output directory (default: output/<book-name>)"
    )
    
    args = parser.parse_args()
    
    book_dir = Path(args.book)
    
    # Validate book folder
    if not book_dir.exists():
        print(f"❌ Book folder not found: {book_dir}")
        sys.exit(1)
    
    manuscript_path = book_dir / "manuscript.md"
    cover_path = book_dir / "cover.png"
    
    # Check for alternative cover formats
    if not cover_path.exists():
        for ext in [".jpg", ".jpeg", ".webp"]:
            alt_cover = book_dir / f"cover{ext}"
            if alt_cover.exists():
                cover_path = alt_cover
                break
    
    if not manuscript_path.exists():
        print(f"❌ manuscript.md not found in {book_dir}")
        sys.exit(1)
    
    if not cover_path.exists():
        print(f"❌ cover image not found in {book_dir}")
        print("   Supported formats: cover.png, cover.jpg, cover.jpeg, cover.webp")
        sys.exit(1)
    
    # Load config
    config_data = load_book_config(book_dir)
    config = SimpleConfig(config_data["title"], config_data["author"])
    
    # Set output directory
    output_dir = Path(args.output) if args.output else Path("output") / book_dir.name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📚 Merging book: {config.title}")
    print(f"👤 Author: {config.author}")
    print(f"📁 Output: {output_dir}")
    print("=" * 50)
    
    # Read manuscript
    content = manuscript_path.read_text(encoding="utf-8")
    
    # Quality check
    print("🔍 Quality check...")
    checker = QualityChecker()
    result = checker.check(content)
    
    if result.warnings:
        print("⚠️ Warnings:")
        for warning in result.warnings:
            print(f"   - {warning}")
    
    print(f"   Word count: {result.word_count}")
    print(f"   Chapter count: {result.chapter_count}")
    print()
    
    # Generate PDFs
    assembler = PDFAssembler(print)
    
    interior_path = assembler.build_interior(config, content, output_dir)
    cover_pdf_path = assembler.build_cover(cover_path, output_dir)
    
    # Copy original files to output
    import shutil
    shutil.copy(manuscript_path, output_dir / "manuscript.md")
    shutil.copy(cover_path, output_dir / cover_path.name)
    
    print("=" * 50)
    print("✅ Merge complete!")
    print(f"📄 Interior PDF: {interior_path}")
    print(f"📄 Cover PDF: {cover_pdf_path}")
    print(f"📁 All files in: {output_dir}")


if __name__ == "__main__":
    main()
