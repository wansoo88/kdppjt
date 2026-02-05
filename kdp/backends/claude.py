"""
Claude Backend
Anthropic Claude API를 통한 LLM 호출
"""

import os
from typing import Optional

from .llm_base import LLMBackend


class ClaudeAPIError(Exception):
    """Claude API 오류"""
    pass


class ClaudeBackend(LLMBackend):
    """Claude 백엔드 구현"""
    
    # Claude 모델별 가격 (USD per 1M tokens)
    PRICING = {
        "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
        "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
        "claude-3-sonnet-20240229": {"input": 3.0, "output": 15.0},
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
    }
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
    ):
        super().__init__()
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self._client = None
        
        if not self.api_key:
            raise ClaudeAPIError(
                "ANTHROPIC_API_KEY가 설정되지 않았습니다.\n"
                "환경 변수 또는 .env 파일에 설정하세요."
            )
    
    @property
    def name(self) -> str:
        return f"claude/{self.model}"
    
    @property
    def client(self):
        """Lazy initialization of Anthropic client"""
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                raise ClaudeAPIError(
                    "anthropic 패키지가 설치되지 않았습니다.\n"
                    "pip install anthropic"
                )
        return self._client
    
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Claude API를 통한 텍스트 생성"""
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt if system_prompt else "You are a helpful assistant.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
        except Exception as e:
            raise ClaudeAPIError(f"Claude API 호출 실패: {e}")
        
        # 토큰 사용량 추적
        input_tokens = message.usage.input_tokens
        output_tokens = message.usage.output_tokens
        self.token_usage.add(input_tokens, output_tokens)
        
        # 응답 텍스트 추출
        return message.content[0].text
    
    def estimate_cost(self) -> float:
        """예상 비용 계산 (USD)"""
        pricing = self.PRICING.get(self.model, {"input": 3.0, "output": 15.0})
        
        input_cost = (self.token_usage.input_tokens / 1_000_000) * pricing["input"]
        output_cost = (self.token_usage.output_tokens / 1_000_000) * pricing["output"]
        
        return input_cost + output_cost
