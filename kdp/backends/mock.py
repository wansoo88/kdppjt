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
        
        # Check for image prompts first (more specific)
        if "image" in prompt_lower and ("prompt" in prompt_lower or "dall-e" in prompt_lower):
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
