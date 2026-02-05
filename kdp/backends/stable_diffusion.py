"""
Stable Diffusion Backend
로컬 Stable Diffusion WebUI API를 통한 이미지 생성
"""

import base64
import os
from typing import Optional, Tuple

import requests

from .image_base import ImageBackend


class StableDiffusionError(Exception):
    """Stable Diffusion 오류"""
    pass


class StableDiffusionBackend(ImageBackend):
    """Stable Diffusion WebUI API 백엔드"""
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv("SD_BASE_URL", "http://localhost:7860")
    
    @property
    def name(self) -> str:
        return "stable-diffusion"
    
    def generate(self, prompt: str, size: Tuple[int, int] = (1024, 1024)) -> bytes:
        """Stable Diffusion WebUI API를 통한 이미지 생성"""
        url = f"{self.base_url}/sdapi/v1/txt2img"
        
        payload = {
            "prompt": prompt,
            "negative_prompt": "blurry, low quality, distorted, watermark, text errors",
            "width": size[0],
            "height": size[1],
            "steps": 30,
            "cfg_scale": 7,
            "sampler_name": "DPM++ 2M Karras",
        }
        
        try:
            response = requests.post(url, json=payload, timeout=300)
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            raise StableDiffusionError(
                f"Stable Diffusion WebUI에 연결할 수 없습니다: {self.base_url}\n"
                "WebUI가 --api 옵션으로 실행 중인지 확인하세요."
            )
        except requests.exceptions.Timeout:
            raise StableDiffusionError("이미지 생성 시간 초과")
        except requests.exceptions.HTTPError as e:
            raise StableDiffusionError(f"Stable Diffusion API 오류: {e}")
        
        data = response.json()
        
        if "images" not in data or not data["images"]:
            raise StableDiffusionError("이미지 생성 실패: 응답에 이미지가 없습니다")
        
        # Base64 디코딩
        image_base64 = data["images"][0]
        return base64.b64decode(image_base64)
    
    def check_connection(self) -> bool:
        """Stable Diffusion WebUI 연결 확인"""
        try:
            response = requests.get(f"{self.base_url}/sdapi/v1/sd-models", timeout=5)
            return response.status_code == 200
        except:
            return False
