"""
Image Backend 추상 클래스
"""

from abc import ABC, abstractmethod
from typing import Tuple


class ImageBackend(ABC):
    """이미지 생성 백엔드 추상 클래스"""
    
    @abstractmethod
    def generate(self, prompt: str, size: Tuple[int, int] = (1024, 1024)) -> bytes:
        """
        이미지 생성
        
        Args:
            prompt: 이미지 생성 프롬프트
            size: 이미지 크기 (width, height)
            
        Returns:
            PNG 이미지 바이트
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """백엔드 이름"""
        pass
