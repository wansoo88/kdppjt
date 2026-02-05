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
        
        if "outline" in prompt.lower():
            response = self._generate_outline()
        elif "chapter" in prompt.lower():
            response = self._generate_chapter(prompt)
        else:
            response = self._generate_generic()
        
        self._output_tokens += len(response.split()) * 2
        return response
    
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
