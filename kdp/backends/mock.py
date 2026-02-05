"""
Mock Backends for Testing
Test backends without external services
"""

from io import BytesIO
from typing import Optional, Tuple
from PIL import Image, ImageDraw

from .llm_base import LLMBackend, TokenUsage
from .image_base import ImageBackend


class MockLLMBackend(LLMBackend):
    """Mock LLM backend for testing"""
    
    def __init__(self):
        self._name = "mock-llm"
        self._input_tokens = 0
        self._output_tokens = 0
    
    @property
    def name(self) -> str:
        return self._name
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        """Mock text generation"""
        self._input_tokens += len(prompt.split()) * 2
        
        prompt_lower = prompt.lower()
        
        # Check for coloring book
        if "coloring book" in prompt_lower and "page ideas" in prompt_lower:
            response = self._generate_coloring_pages()
        elif "coloring book" in prompt_lower and "prompt" in prompt_lower:
            response = self._generate_coloring_prompts()
        # Check for image prompts (more specific)
        elif "image" in prompt_lower and ("prompt" in prompt_lower or "dall-e" in prompt_lower):
            response = self._generate_image_prompts()
        elif "edit" in prompt_lower and "polish" not in prompt_lower:
            response = self._generate_edited_story()
        elif "picture book" in prompt_lower or ("pages" in prompt_lower and "write" in prompt_lower):
            response = self._generate_story()
        elif "outline" in prompt_lower:
            response = self._generate_outline()
        elif "chapter" in prompt_lower:
            response = self._generate_chapter(prompt)
        else:
            response = self._generate_generic()
        
        self._output_tokens += len(response.split()) * 2
        return response
    
    def _generate_coloring_pages(self) -> str:
        return '''{
  "title": "Coloring Book for Nurses: Relaxation & Self-Care",
  "pages": [
    {"page": 1, "title": "Healing Hands", "description": "Intricate design of caring hands with floral patterns", "type": "pattern"},
    {"page": 2, "title": "Stethoscope Mandala", "description": "Mandala design incorporating stethoscope and medical symbols", "type": "mandala"},
    {"page": 3, "title": "Coffee Break", "description": "Cozy scene of coffee cup with steam swirls and pastries", "type": "scene"},
    {"page": 4, "title": "You Are Appreciated", "description": "Inspirational quote with decorative lettering and flowers", "type": "quote"},
    {"page": 5, "title": "Night Shift Stars", "description": "Peaceful night sky with moon and stars pattern", "type": "pattern"},
    {"page": 6, "title": "Scrubs & Flowers", "description": "Nurse scrubs decorated with botanical flower patterns", "type": "scene"},
    {"page": 7, "title": "Heart Monitor Art", "description": "Creative heartbeat line transforming into flowers", "type": "pattern"},
    {"page": 8, "title": "Self-Care Sunday", "description": "Relaxing bath scene with candles and plants", "type": "scene"},
    {"page": 9, "title": "Medical Mandala", "description": "Symmetrical mandala with pills, bandages, and hearts", "type": "mandala"},
    {"page": 10, "title": "Heroes Wear Scrubs", "description": "Bold lettering with cape and medical symbols", "type": "quote"},
    {"page": 11, "title": "Garden of Healing", "description": "Peaceful garden scene with medicinal herbs", "type": "scene"},
    {"page": 12, "title": "Nurse Life Pattern", "description": "Repeating pattern of nursing items and symbols", "type": "pattern"},
    {"page": 13, "title": "Breathe", "description": "Calming word art with flowing air and leaf designs", "type": "quote"},
    {"page": 14, "title": "Caring Heart", "description": "Large decorative heart filled with intricate patterns", "type": "mandala"},
    {"page": 15, "title": "Tea Time", "description": "Cozy tea set with cookies and flowers", "type": "scene"},
    {"page": 16, "title": "Butterfly Transformation", "description": "Butterflies emerging from medical symbols", "type": "pattern"},
    {"page": 17, "title": "You Make a Difference", "description": "Uplifting quote with sunburst design", "type": "quote"},
    {"page": 18, "title": "Peaceful Pond", "description": "Serene water scene with lotus flowers", "type": "scene"},
    {"page": 19, "title": "Nurse Badge Mandala", "description": "Circular design around a nurse ID badge", "type": "mandala"},
    {"page": 20, "title": "Comfort & Care", "description": "Warm blanket pattern with hearts", "type": "pattern"},
    {"page": 21, "title": "Sunrise Hope", "description": "Beautiful sunrise over hospital silhouette", "type": "scene"},
    {"page": 22, "title": "Strength in Kindness", "description": "Decorative lettering with ribbon design", "type": "quote"},
    {"page": 23, "title": "Floral Scrub Cap", "description": "Detailed scrub cap covered in flower patterns", "type": "pattern"},
    {"page": 24, "title": "Zen Garden", "description": "Japanese zen garden with stones and raked sand", "type": "scene"},
    {"page": 25, "title": "Heartbeat Flowers", "description": "EKG line blooming into various flowers", "type": "pattern"},
    {"page": 26, "title": "Rest & Recharge", "description": "Cozy bedroom scene with plants and books", "type": "scene"},
    {"page": 27, "title": "Compassion Mandala", "description": "Intricate mandala with hands and hearts", "type": "mandala"},
    {"page": 28, "title": "One Day at a Time", "description": "Calendar page with floral decorations", "type": "quote"},
    {"page": 29, "title": "Healing Garden", "description": "Greenhouse full of medicinal plants", "type": "scene"},
    {"page": 30, "title": "Thank You Nurses", "description": "Celebratory design with confetti and hearts", "type": "pattern"}
  ]
}'''

    def _generate_coloring_prompts(self) -> str:
        return '''{
  "cover_prompt": "Colorful illustrated book cover for nurses coloring book, warm and inviting design with stethoscope, hearts, and flowers, professional yet caring aesthetic, title space at top",
  "pages": [
    {"page": 1, "prompt": "Black and white line art, coloring book page, intricate design of two caring hands with detailed floral and vine patterns flowing around them, clean outlines, white background, no shading"},
    {"page": 2, "prompt": "Black and white line art, coloring book page, mandala design with stethoscope forming the center, surrounded by medical crosses, hearts, and geometric patterns, symmetrical, white background"},
    {"page": 3, "prompt": "Black and white line art, coloring book page, cozy coffee cup with decorative steam swirls, surrounded by pastries and small flowers, detailed line work, white background"},
    {"page": 4, "prompt": "Black and white line art, coloring book page, decorative hand lettering saying You Are Appreciated surrounded by roses and leaves, ornate border, white background"},
    {"page": 5, "prompt": "Black and white line art, coloring book page, night sky pattern with crescent moon, detailed stars, and swirling clouds, dreamy design, white background"},
    {"page": 6, "prompt": "Black and white line art, coloring book page, nurse scrubs top decorated with detailed botanical flower patterns, buttons and pockets visible, white background"},
    {"page": 7, "prompt": "Black and white line art, coloring book page, creative EKG heartbeat line that transforms into blooming flowers and vines, flowing design, white background"},
    {"page": 8, "prompt": "Black and white line art, coloring book page, relaxing bath scene with clawfoot tub, candles, potted plants, and bubbles, peaceful atmosphere, white background"},
    {"page": 9, "prompt": "Black and white line art, coloring book page, symmetrical mandala incorporating pills, bandages, medical crosses, and hearts in geometric pattern, white background"},
    {"page": 10, "prompt": "Black and white line art, coloring book page, bold decorative lettering Heroes Wear Scrubs with flowing cape design and small medical symbols, white background"},
    {"page": 11, "prompt": "Black and white line art, coloring book page, peaceful garden scene with labeled medicinal herbs like lavender, chamomile, and mint, detailed botanical style, white background"},
    {"page": 12, "prompt": "Black and white line art, coloring book page, seamless repeating pattern of nursing items: stethoscopes, syringes, bandages, hearts, pills, white background"},
    {"page": 13, "prompt": "Black and white line art, coloring book page, the word BREATHE in decorative lettering with flowing air swirls and delicate leaves, calming design, white background"},
    {"page": 14, "prompt": "Black and white line art, coloring book page, large decorative heart shape filled with intricate zentangle patterns, swirls and geometric designs, white background"},
    {"page": 15, "prompt": "Black and white line art, coloring book page, detailed tea set with teapot, cups, cookies on plate, and small flowers, cozy scene, white background"},
    {"page": 16, "prompt": "Black and white line art, coloring book page, butterflies with detailed wing patterns emerging from and flying around medical symbols, transformation theme, white background"},
    {"page": 17, "prompt": "Black and white line art, coloring book page, You Make a Difference in decorative script with radiating sunburst lines and small stars, white background"},
    {"page": 18, "prompt": "Black and white line art, coloring book page, serene pond scene with detailed lotus flowers, lily pads, and gentle ripples, peaceful design, white background"},
    {"page": 19, "prompt": "Black and white line art, coloring book page, circular mandala design with nurse ID badge at center, surrounded by symmetrical patterns and medical symbols, white background"},
    {"page": 20, "prompt": "Black and white line art, coloring book page, cozy knitted blanket pattern with hearts and geometric designs, warm and comforting, white background"},
    {"page": 21, "prompt": "Black and white line art, coloring book page, beautiful sunrise with detailed rays over hospital building silhouette, hopeful scene, white background"},
    {"page": 22, "prompt": "Black and white line art, coloring book page, Strength in Kindness in elegant lettering with flowing ribbon design and small flowers, white background"},
    {"page": 23, "prompt": "Black and white line art, coloring book page, detailed surgical scrub cap covered in various flower patterns, roses, daisies, and leaves, white background"},
    {"page": 24, "prompt": "Black and white line art, coloring book page, Japanese zen garden with carefully placed stones, raked sand patterns, and small bridge, peaceful, white background"},
    {"page": 25, "prompt": "Black and white line art, coloring book page, EKG heartbeat line that blooms into various detailed flowers: roses, tulips, daisies, flowing design, white background"},
    {"page": 26, "prompt": "Black and white line art, coloring book page, cozy bedroom scene with bed, nightstand, potted plants, books, and window with curtains, restful, white background"},
    {"page": 27, "prompt": "Black and white line art, coloring book page, intricate mandala with caring hands reaching toward center, surrounded by hearts and flowing patterns, white background"},
    {"page": 28, "prompt": "Black and white line art, coloring book page, One Day at a Time in decorative lettering on calendar page design with floral corner decorations, white background"},
    {"page": 29, "prompt": "Black and white line art, coloring book page, greenhouse interior full of potted medicinal plants and herbs, detailed botanical illustration style, white background"},
    {"page": 30, "prompt": "Black and white line art, coloring book page, Thank You Nurses in celebratory lettering with confetti, hearts, stars, and ribbon decorations, white background"}
  ]
}'''
    
    def _generate_story(self) -> str:
        return '''{
  "title": "The Brave Little Rabbit",
  "pages": [
    {"page": 1, "text": "In a cozy burrow under the old oak tree, lived a small rabbit named Pip. Pip had the softest brown fur and the biggest dreams.", "emotion": "warmth", "scene": "Cozy underground burrow with warm lighting"},
    {"page": 2, "text": "One sunny morning, Pip heard whispers about a magical garden beyond the meadow. \\"I must find it!\\" Pip exclaimed.", "emotion": "curiosity", "scene": "Rabbit at burrow entrance, looking at distant meadow"},
    {"page": 3, "text": "The path was long and winding. Pip hopped over streams and under fallen logs. Sometimes the shadows seemed scary.", "emotion": "determination", "scene": "Rabbit hopping through forest path"},
    {"page": 4, "text": "A wise old owl hooted from above. \\"Little one, the garden is closer than you think. Follow your heart.\\"", "emotion": "wonder", "scene": "Owl on branch talking to rabbit below"},
    {"page": 5, "text": "Pip felt tired and almost gave up. But then, a beautiful butterfly appeared, dancing in the sunlight.", "emotion": "hope", "scene": "Tired rabbit watching colorful butterfly"},
    {"page": 6, "text": "Following the butterfly, Pip pushed through the last bushes and gasped. The magical garden was real!", "emotion": "joy", "scene": "Rabbit discovering beautiful garden"},
    {"page": 7, "text": "Flowers of every color swayed in the breeze. Pip had never seen anything so beautiful in all his life.", "emotion": "awe", "scene": "Wide view of magical garden with flowers"},
    {"page": 8, "text": "Pip made friends with the garden creatures - a ladybug, a friendly frog, and a singing bluebird.", "emotion": "friendship", "scene": "Rabbit with garden animal friends"},
    {"page": 9, "text": "As the sun began to set, Pip knew it was time to go home. But this adventure would never be forgotten.", "emotion": "bittersweet", "scene": "Sunset over garden, rabbit looking back"},
    {"page": 10, "text": "Pip hopped back through the forest, heart full of joy. The scary shadows didn't seem so scary anymore.", "emotion": "confidence", "scene": "Rabbit confidently hopping through forest"},
    {"page": 11, "text": "Back at the cozy burrow, Pip told everyone about the magical garden. \\"And I'll go back again!\\" Pip promised.", "emotion": "excitement", "scene": "Rabbit telling story to family in burrow"},
    {"page": 12, "text": "That night, Pip dreamed of flowers and friends, knowing that brave hearts always find magic. The End.", "emotion": "contentment", "scene": "Sleeping rabbit with dream clouds above"}
  ]
}'''

    def _generate_edited_story(self) -> str:
        return self._generate_story()
    
    def _generate_image_prompts(self) -> str:
        return '''{
  "cover_prompt": "Children's book cover illustration, a cute brown rabbit standing at the entrance of a magical garden filled with colorful flowers, warm golden sunlight, soft watercolor style, whimsical and inviting, no text",
  "pages": [
    {"page": 1, "prompt": "Children's book illustration, cozy underground rabbit burrow with warm orange lighting, small brown rabbit with big eyes sitting on a tiny bed, roots visible on ceiling, soft watercolor style, warm and inviting atmosphere"},
    {"page": 2, "prompt": "Children's book illustration, small brown rabbit at burrow entrance looking out at a vast sunny meadow, morning light, sense of wonder and adventure, soft watercolor style"},
    {"page": 3, "prompt": "Children's book illustration, determined small rabbit hopping along a winding forest path, dappled sunlight through trees, fallen logs and small stream, soft watercolor style"},
    {"page": 4, "prompt": "Children's book illustration, wise old owl with kind eyes perched on a branch, looking down at small rabbit below, magical forest atmosphere, moonlight filtering through leaves, soft watercolor style"},
    {"page": 5, "prompt": "Children's book illustration, tired small rabbit sitting on a rock, beautiful colorful butterfly dancing in a beam of sunlight, hope and magic in the air, soft watercolor style"},
    {"page": 6, "prompt": "Children's book illustration, small rabbit pushing through bushes discovering a magnificent magical garden, expression of pure joy and wonder, vibrant colors, soft watercolor style"},
    {"page": 7, "prompt": "Children's book illustration, wide panoramic view of magical garden with flowers of every color, rabbit small in the scene looking around in awe, dreamy atmosphere, soft watercolor style"},
    {"page": 8, "prompt": "Children's book illustration, rabbit surrounded by friendly garden creatures - red ladybug, green frog, blue singing bird, all smiling, friendship and joy, soft watercolor style"},
    {"page": 9, "prompt": "Children's book illustration, beautiful sunset over magical garden, small rabbit at the edge looking back with bittersweet expression, golden and pink sky, soft watercolor style"},
    {"page": 10, "prompt": "Children's book illustration, confident rabbit hopping through forest path, warm evening light, shadows no longer scary, sense of growth and bravery, soft watercolor style"},
    {"page": 11, "prompt": "Children's book illustration, rabbit family gathered in cozy burrow, main rabbit telling story with animated gestures, other rabbits listening with wonder, warm lighting, soft watercolor style"},
    {"page": 12, "prompt": "Children's book illustration, sleeping rabbit in cozy bed, dream cloud above showing flowers and friends from the adventure, peaceful and content, soft watercolor style, gentle night lighting"}
  ]
}'''
    
    def _generate_outline(self) -> str:
        return """# Table of Contents

## Chapter 1: Introduction
Basic concepts of cloud computing and AWS services overview

## Chapter 2: Core Services
How to use EC2, S3, RDS and other core services

## Chapter 3: Architecture Design
Scalable architecture design patterns

## Chapter 4: Security
IAM and security best practices

## Chapter 5: Real Projects
Practical project implementation examples"""

    def _generate_chapter(self, prompt: str) -> str:
        chapter_num = "1"
        for word in prompt.split():
            if word.isdigit():
                chapter_num = word
                break
        
        return f"""# Chapter {chapter_num}: Understanding Cloud Architecture

## Overview

This chapter covers the core concepts of cloud architecture.
Cloud has become an essential element in modern application development.

## Key Concepts

Cloud computing is a way of providing computing resources over the internet.
The main advantages include scalability, cost efficiency, and flexibility.

### Scalability

Resources can be dynamically adjusted as needed.
When traffic increases, servers are automatically added,
and when it decreases, they can be reduced to optimize costs.

### Cost Efficiency

Pay-as-you-go model where you only pay for what you use.
You can start services without initial infrastructure investment.

## Practical Example

Here is a simple architecture configuration example:

```
[User] -> [Load Balancer] -> [Web Server] -> [Database]
```

## Summary

In this chapter, we learned the basic concepts of cloud architecture.
In the next chapter, we will explore specific service usage methods.
"""

    def _generate_generic(self) -> str:
        return """Cloud computing is at the core of modern IT infrastructure.
Major cloud providers like AWS, Azure, and GCP offer various services.
This allows companies to reduce infrastructure management burden and focus on core business."""

    def get_token_usage(self) -> TokenUsage:
        return {
            "input_tokens": self._input_tokens,
            "output_tokens": self._output_tokens,
        }


class MockImageBackend(ImageBackend):
    """Mock image backend for testing"""
    
    def __init__(self):
        self._name = "mock-image"
    
    @property
    def name(self) -> str:
        return self._name
    
    def generate(self, prompt: str, size: Tuple[int, int] = (1024, 1024)) -> bytes:
        """Generate placeholder image and return as bytes"""
        width, height = size
        
        # Create gradient background
        img = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(img)
        
        for y in range(height):
            r = int(50 + (y / height) * 100)
            g = int(80 + (y / height) * 80)
            b = int(120 + (y / height) * 60)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        
        # Center text area
        center_y = height // 2
        draw.rectangle(
            [(100, center_y - 100), (width - 100, center_y + 100)],
            fill=(255, 255, 255),
            outline=(200, 200, 200),
        )
        
        # "MOCK COVER" text
        text = "MOCK COVER"
        text_bbox = draw.textbbox((0, 0), text)
        text_width = text_bbox[2] - text_bbox[0]
        text_x = (width - text_width) // 2
        draw.text((text_x, center_y - 10), text, fill=(50, 50, 50))
        
        # Convert to PNG bytes
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()
