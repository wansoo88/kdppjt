"""
AI Backend Modules
LLM 및 이미지 생성 백엔드
"""

from .llm_base import LLMBackend, TokenUsage
from .ollama import OllamaBackend, OllamaConnectionError
from .claude import ClaudeBackend, ClaudeAPIError
from .image_base import ImageBackend
from .stable_diffusion import StableDiffusionBackend
from .mock import MockLLMBackend, MockImageBackend

__all__ = [
    "LLMBackend",
    "TokenUsage",
    "OllamaBackend",
    "OllamaConnectionError",
    "ClaudeBackend",
    "ClaudeAPIError",
    "ImageBackend",
    "StableDiffusionBackend",
    "MockLLMBackend",
    "MockImageBackend",
    "create_llm_backend",
    "create_image_backend",
]


def create_llm_backend(backend_type: str, **kwargs) -> LLMBackend:
    """
    LLM 백엔드 팩토리 함수
    
    Args:
        backend_type: 백엔드 타입 ("ollama" | "claude" | "mock")
        **kwargs: 백엔드별 추가 인자
        
    Returns:
        LLMBackend 인스턴스
    """
    backend_type = backend_type.lower()
    
    if backend_type == "ollama":
        return OllamaBackend(
            model=kwargs.get("model", "llama3.1"),
            base_url=kwargs.get("base_url"),
        )
    elif backend_type == "claude":
        return ClaudeBackend(
            api_key=kwargs.get("api_key"),
            model=kwargs.get("model", "claude-3-5-sonnet-20241022"),
        )
    elif backend_type == "mock":
        return MockLLMBackend()
    else:
        raise ValueError(
            f"지원하지 않는 백엔드: {backend_type}\n"
            "지원 백엔드: ollama, claude, mock"
        )


def create_image_backend(backend_type: str, **kwargs) -> ImageBackend:
    """
    이미지 백엔드 팩토리 함수
    
    Args:
        backend_type: 백엔드 타입 ("stable_diffusion" | "mock")
        **kwargs: 백엔드별 추가 인자
        
    Returns:
        ImageBackend 인스턴스
    """
    backend_type = backend_type.lower()
    
    if backend_type == "stable_diffusion" or backend_type == "sd":
        return StableDiffusionBackend(
            base_url=kwargs.get("base_url"),
        )
    elif backend_type == "mock":
        return MockImageBackend()
    else:
        raise ValueError(
            f"지원하지 않는 이미지 백엔드: {backend_type}\n"
            "지원 백엔드: stable_diffusion, mock"
        )
