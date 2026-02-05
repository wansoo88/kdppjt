"""
LLM Backend 추상 클래스
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class TokenUsage:
    """토큰 사용량 추적"""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    
    def add(self, input_tokens: int, output_tokens: int):
        """토큰 사용량 추가"""
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_tokens = self.input_tokens + self.output_tokens


class LLMBackend(ABC):
    """LLM 백엔드 추상 클래스"""
    
    def __init__(self):
        self.token_usage = TokenUsage()
    
    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """
        텍스트 생성
        
        Args:
            prompt: 사용자 프롬프트
            system_prompt: 시스템 프롬프트 (선택)
            
        Returns:
            생성된 텍스트
        """
        pass
    
    def get_token_usage(self) -> dict:
        """토큰 사용량 반환"""
        return {
            "input_tokens": self.token_usage.input_tokens,
            "output_tokens": self.token_usage.output_tokens,
            "total_tokens": self.token_usage.total_tokens,
        }
    
    def reset_token_usage(self):
        """토큰 사용량 초기화"""
        self.token_usage = TokenUsage()
    
    @property
    @abstractmethod
    def name(self) -> str:
        """백엔드 이름"""
        pass
