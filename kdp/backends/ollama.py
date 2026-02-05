"""
Ollama Backend
로컬 Ollama 서버를 통한 LLM 호출
"""

import os
import requests
from typing import Optional

from .llm_base import LLMBackend


class OllamaConnectionError(Exception):
    """Ollama 서버 연결 오류"""
    pass


class OllamaBackend(LLMBackend):
    """Ollama 백엔드 구현"""
    
    def __init__(
        self,
        model: str = "llama3.1",
        base_url: Optional[str] = None,
    ):
        super().__init__()
        self.model = model
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    @property
    def name(self) -> str:
        return f"ollama/{self.model}"
    
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Ollama API를 통한 텍스트 생성"""
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            response = requests.post(url, json=payload, timeout=300)
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            raise OllamaConnectionError(
                f"Ollama 서버에 연결할 수 없습니다: {self.base_url}\n"
                "Ollama가 실행 중인지 확인하세요: ollama serve"
            )
        except requests.exceptions.Timeout:
            raise OllamaConnectionError("Ollama 요청 시간 초과")
        except requests.exceptions.HTTPError as e:
            raise OllamaConnectionError(f"Ollama API 오류: {e}")
        
        data = response.json()
        
        # 토큰 사용량 추적 (Ollama는 대략적인 추정)
        # Ollama API는 정확한 토큰 수를 제공하지 않으므로 문자 수 기반 추정
        input_tokens = len(prompt) // 4
        output_tokens = len(data.get("response", "")) // 4
        self.token_usage.add(input_tokens, output_tokens)
        
        return data.get("response", "")
    
    def check_connection(self) -> bool:
        """Ollama 서버 연결 확인"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def list_models(self) -> list[str]:
        """사용 가능한 모델 목록"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
        except:
            return []
