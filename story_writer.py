#!/usr/bin/env python3
"""
KDP Story Writer - 3-Stage Writing System
1. Draft: Sentence variety, emotional depth
2. First Edit: Grammar, flow
3. Final Edit: Pro quality, consistency

Usage:
    python story_writer.py --book books/my-book --topic "A brave rabbit's adventure"
    python story_writer.py --book books/my-book --topic "..." --pages 12
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
class StoryConfig:
    """Story configuration"""
    topic: str
    genre: str = "children"
    target_age: str = "4-8"
    pages: int = 12
    language: str = "en"
    style: str = "warm and engaging"


class StoryWriter:
    """3-Stage Story Writing System"""
    
    def __init__(self, llm_backend: str = "ollama", progress_callback=None):
        self.llm = create_llm_backend(llm_backend)
        self.log = progress_callback or print
    
    def stage1_draft(self, config: StoryConfig) -> list[dict]:
        """Stage 1: Draft - Focus on variety and emotion"""
        self.log("📝 Stage 1: Creating draft (variety & emotion)...")
        
        prompt = f"""You are a children's book author. Write a {config.pages}-page picture book story.

Topic: {config.topic}
Target Age: {config.target_age}
Style: {config.style}

Requirements:
- Each page: 2-4 sentences (suitable for picture book)
- Use varied sentence structures (short, long, questions, exclamations)
- Include emotional moments (joy, surprise, worry, relief, triumph)
- Create vivid, imaginable scenes for each page
- Build tension and resolution

Output as JSON:
{{
  "title": "Story Title",
  "pages": [
    {{"page": 1, "text": "Page text...", "emotion": "curiosity", "scene": "Brief scene description"}},
    ...
  ]
}}"""

        response = self.llm.generate(prompt, max_tokens=4000)
        return self._parse_json(response)
    
    def stage2_first_edit(self, draft: dict) -> dict:
        """Stage 2: First Edit - Grammar and flow"""
        self.log("✏️ Stage 2: First edit (grammar & flow)...")
        
        prompt = f"""You are a professional editor. Edit this children's book for grammar and flow.

Current draft:
{json.dumps(draft, indent=2, ensure_ascii=False)}

Edit for:
1. Fix any grammar issues
2. Improve sentence flow and rhythm
3. Ensure smooth transitions between pages
4. Make language age-appropriate
5. Keep the emotional beats intact

Return the edited version in the same JSON format."""

        response = self.llm.generate(prompt, max_tokens=4000)
        return self._parse_json(response)
    
    def stage3_final_edit(self, edited: dict) -> dict:
        """Stage 3: Final Edit - Pro quality and consistency"""
        self.log("🎯 Stage 3: Final edit (pro quality & consistency)...")
        
        prompt = f"""You are a senior publishing editor. Do a final polish on this children's book.

Current version:
{json.dumps(edited, indent=2, ensure_ascii=False)}

Final polish for:
1. Professional publishing quality
2. Consistent voice and tone throughout
3. Perfect pacing for read-aloud
4. Memorable, quotable phrases
5. Strong opening and satisfying ending
6. Character consistency

Return the final version in the same JSON format."""

        response = self.llm.generate(prompt, max_tokens=4000)
        return self._parse_json(response)
    
    def generate_image_prompts(self, story: dict) -> list[dict]:
        """Generate ChatGPT/DALL-E image prompts for each page"""
        self.log("🎨 Generating image prompts...")
        
        prompt = f"""Create detailed image generation prompts for each page of this children's book.

Story:
{json.dumps(story, indent=2, ensure_ascii=False)}

For each page, create a DALL-E/ChatGPT image prompt that:
- Describes the scene in vivid detail
- Specifies art style: "children's book illustration, warm colors, soft lighting"
- Includes character descriptions consistently
- Mentions composition (close-up, wide shot, etc.)
- Avoids text in the image

Output as JSON:
{{
  "cover_prompt": "Cover image prompt...",
  "pages": [
    {{"page": 1, "prompt": "Detailed image prompt..."}},
    ...
  ]
}}"""

        response = self.llm.generate(prompt, max_tokens=4000)
        return self._parse_json(response)
    
    def _parse_json(self, response: str) -> dict:
        """Extract JSON from LLM response"""
        import re
        # Find JSON block
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Return as-is if parsing fails
        return {"raw": response}
    
    def write_story(self, config: StoryConfig) -> tuple[dict, dict]:
        """Run full 3-stage writing process"""
        self.log(f"📚 Starting story: {config.topic}")
        self.log("=" * 50)
        
        # Stage 1: Draft
        draft = self.stage1_draft(config)
        
        # Stage 2: First Edit
        edited = self.stage2_first_edit(draft)
        
        # Stage 3: Final Edit
        final = self.stage3_final_edit(edited)
        
        # Generate image prompts
        image_prompts = self.generate_image_prompts(final)
        
        self.log("=" * 50)
        self.log("✅ Story writing complete!")
        
        return final, image_prompts


def save_manuscript(story: dict, output_dir: Path):
    """Save story as manuscript.md"""
    lines = [f"# {story.get('title', 'Untitled Story')}\n"]
    
    for page in story.get("pages", []):
        page_num = page.get("page", "?")
        text = page.get("text", "")
        lines.append(f"\n## Page {page_num}\n")
        lines.append(f"{text}\n")
    
    manuscript_path = output_dir / "manuscript.md"
    manuscript_path.write_text("\n".join(lines), encoding="utf-8")
    return manuscript_path


def save_image_prompts(prompts: dict, output_dir: Path):
    """Save image prompts for ChatGPT use"""
    lines = ["# Image Prompts for ChatGPT/DALL-E\n"]
    lines.append("Copy each prompt to ChatGPT to generate images.\n")
    lines.append("=" * 50 + "\n")
    
    # Cover prompt
    cover_prompt = prompts.get("cover_prompt", "")
    if cover_prompt:
        lines.append("## Cover Image\n")
        lines.append(f"```\n{cover_prompt}\n```\n")
    
    # Page prompts
    pages = prompts.get("pages", [])
    for page in pages:
        page_num = page.get("page", "?")
        prompt = page.get("prompt", "")
        lines.append(f"\n## Page {page_num}\n")
        lines.append(f"```\n{prompt}\n```\n")
    
    prompts_path = output_dir / "image_prompts.md"
    prompts_path.write_text("\n".join(lines), encoding="utf-8")
    return prompts_path


def save_story_json(story: dict, prompts: dict, output_dir: Path):
    """Save raw JSON data"""
    data = {
        "story": story,
        "image_prompts": prompts
    }
    json_path = output_dir / "story_data.json"
    json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return json_path


def main():
    parser = argparse.ArgumentParser(
        description="3-Stage Story Writer for KDP Picture Books",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
    python story_writer.py --book books/rabbit-adventure --topic "A brave rabbit discovers a magical garden"
    python story_writer.py --book books/my-story --topic "..." --pages 10 --backend mock
        """
    )
    
    parser.add_argument("--book", "-b", required=True, help="Book folder path")
    parser.add_argument("--topic", "-t", required=True, help="Story topic/premise")
    parser.add_argument("--pages", "-p", type=int, default=12, help="Number of pages (default: 12)")
    parser.add_argument("--age", default="4-8", help="Target age range (default: 4-8)")
    parser.add_argument("--backend", default="ollama", help="LLM backend: ollama, claude, mock")
    
    args = parser.parse_args()
    
    # Setup
    book_dir = Path(args.book)
    book_dir.mkdir(parents=True, exist_ok=True)
    
    config = StoryConfig(
        topic=args.topic,
        pages=args.pages,
        target_age=args.age
    )
    
    try:
        writer = StoryWriter(llm_backend=args.backend)
        story, image_prompts = writer.write_story(config)
        
        # Save outputs
        manuscript_path = save_manuscript(story, book_dir)
        prompts_path = save_image_prompts(image_prompts, book_dir)
        json_path = save_story_json(story, image_prompts, book_dir)
        
        print(f"\n📄 Manuscript: {manuscript_path}")
        print(f"🎨 Image prompts: {prompts_path}")
        print(f"📊 Raw data: {json_path}")
        print(f"\n💡 Next steps:")
        print(f"   1. Open {prompts_path} and copy prompts to ChatGPT")
        print(f"   2. Save generated images as cover.png and page images")
        print(f"   3. Run: python merge.py --book {book_dir}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
