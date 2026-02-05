#!/usr/bin/env python3
"""
KDP Coloring Book Generator
Generate coloring book pages with themes and image prompts

Usage:
    python coloring_book.py --book books/nurse-coloring --theme "nurses" --pages 30
"""

import argparse
import json
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from kdp.backends import create_llm_backend


@dataclass
class ColoringBookConfig:
    """Coloring book configuration"""
    theme: str
    pages: int = 30
    style: str = "line art"
    difficulty: str = "medium"  # simple, medium, detailed


class ColoringBookGenerator:
    """Coloring Book Page Generator"""
    
    def __init__(self, llm_backend: str = "ollama", progress_callback=None):
        self.llm = create_llm_backend(llm_backend)
        self.log = progress_callback or print
    
    def generate_page_ideas(self, config: ColoringBookConfig) -> list[dict]:
        """Generate page ideas for coloring book"""
        self.log(f"📝 Generating {config.pages} page ideas for '{config.theme}' coloring book...")
        
        prompt = f"""You are a coloring book designer. Create {config.pages} unique page ideas for an adult coloring book.

Theme: {config.theme}
Difficulty: {config.difficulty}

Requirements:
- Each page should be unique and interesting
- Include variety: scenes, patterns, objects, inspirational quotes
- Consider the target audience (nurses/healthcare workers)
- Mix detailed illustrations with simpler designs for variety

Output as JSON:
{{
  "title": "Coloring Book Title",
  "pages": [
    {{"page": 1, "title": "Page title", "description": "Brief description", "type": "scene|pattern|quote|mandala"}},
    ...
  ]
}}"""

        response = self.llm.generate(prompt, max_tokens=4000)
        return self._parse_json(response)
    
    def generate_image_prompts(self, pages: dict, config: ColoringBookConfig) -> dict:
        """Generate DALL-E/ChatGPT prompts for coloring pages"""
        self.log("🎨 Generating image prompts...")
        
        prompt = f"""Create detailed image generation prompts for each coloring book page.

Theme: {config.theme}
Style: Black and white line art for coloring
Pages: {json.dumps(pages, indent=2, ensure_ascii=False)}

For each page, create a prompt that:
- Specifies "black and white line art, coloring book page"
- Has clean outlines suitable for coloring
- NO shading, NO gradients, NO filled areas
- White background
- Clear, distinct lines
- Appropriate complexity for adults

Output as JSON:
{{
  "cover_prompt": "Cover image prompt (can be colored)...",
  "pages": [
    {{"page": 1, "prompt": "Black and white line art, coloring book page, ..."}},
    ...
  ]
}}"""

        response = self.llm.generate(prompt, max_tokens=6000)
        return self._parse_json(response)
    
    def _parse_json(self, response: str) -> dict:
        """Extract JSON from LLM response"""
        import re
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        return {"raw": response}
    
    def generate(self, config: ColoringBookConfig) -> tuple[dict, dict]:
        """Generate complete coloring book"""
        self.log(f"📚 Creating coloring book: {config.theme}")
        self.log("=" * 50)
        
        # Generate page ideas
        pages = self.generate_page_ideas(config)
        
        # Generate image prompts
        prompts = self.generate_image_prompts(pages, config)
        
        self.log("=" * 50)
        self.log("✅ Coloring book generation complete!")
        
        return pages, prompts


def save_coloring_book(pages: dict, output_dir: Path):
    """Save coloring book structure"""
    lines = [f"# {pages.get('title', 'Coloring Book')}\n"]
    lines.append("A coloring book for relaxation and stress relief.\n")
    
    for page in pages.get("pages", []):
        page_num = page.get("page", "?")
        title = page.get("title", "")
        desc = page.get("description", "")
        page_type = page.get("type", "")
        
        lines.append(f"\n## Page {page_num}: {title}\n")
        lines.append(f"Type: {page_type}\n")
        lines.append(f"{desc}\n")
    
    path = output_dir / "manuscript.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def save_image_prompts(prompts: dict, output_dir: Path):
    """Save image prompts for ChatGPT"""
    lines = ["# Coloring Book Image Prompts\n"]
    lines.append("Copy each prompt to ChatGPT/DALL-E to generate coloring pages.\n")
    lines.append("**Important:** Request 'black and white line art' for coloring pages.\n")
    lines.append("=" * 50 + "\n")
    
    # Cover
    cover = prompts.get("cover_prompt", "")
    if cover:
        lines.append("## Cover (Can be colored)\n")
        lines.append(f"```\n{cover}\n```\n")
    
    # Pages
    for page in prompts.get("pages", []):
        page_num = page.get("page", "?")
        prompt = page.get("prompt", "")
        lines.append(f"\n## Page {page_num}\n")
        lines.append(f"```\n{prompt}\n```\n")
    
    path = output_dir / "image_prompts.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main():
    parser = argparse.ArgumentParser(
        description="Generate Coloring Book for KDP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
    python coloring_book.py --book books/nurse-coloring --theme "nurses and healthcare" --pages 30
    python coloring_book.py --book books/flowers --theme "botanical flowers" --pages 25 --backend mock
        """
    )
    
    parser.add_argument("--book", "-b", required=True, help="Book folder path")
    parser.add_argument("--theme", "-t", required=True, help="Coloring book theme")
    parser.add_argument("--pages", "-p", type=int, default=30, help="Number of pages (default: 30)")
    parser.add_argument("--difficulty", "-d", default="medium", choices=["simple", "medium", "detailed"])
    parser.add_argument("--backend", default="ollama", help="LLM backend: ollama, claude, mock")
    
    args = parser.parse_args()
    
    book_dir = Path(args.book)
    book_dir.mkdir(parents=True, exist_ok=True)
    
    config = ColoringBookConfig(
        theme=args.theme,
        pages=args.pages,
        difficulty=args.difficulty
    )
    
    try:
        generator = ColoringBookGenerator(llm_backend=args.backend)
        pages, prompts = generator.generate(config)
        
        # Save outputs
        manuscript_path = save_coloring_book(pages, book_dir)
        prompts_path = save_image_prompts(prompts, book_dir)
        
        # Save raw JSON
        json_path = book_dir / "coloring_data.json"
        json_path.write_text(json.dumps({"pages": pages, "prompts": prompts}, indent=2, ensure_ascii=False), encoding="utf-8")
        
        print(f"\n📄 Structure: {manuscript_path}")
        print(f"🎨 Image prompts: {prompts_path}")
        print(f"📊 Raw data: {json_path}")
        print(f"\n💡 Next steps:")
        print(f"   1. Open {prompts_path} and copy prompts to ChatGPT")
        print(f"   2. Save generated images (black & white line art)")
        print(f"   3. Add cover.png and run: python merge.py --book {book_dir}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
