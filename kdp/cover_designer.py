"""
표지 디자이너
이미지 생성 백엔드를 사용하여 책 표지 생성
"""

from pathlib import Path
from typing import Callable, Optional

from .config import BookConfig
from .backends import ImageBackend


class CoverDesigner:
    """책 표지 디자이너"""
    
    # 장르별 프롬프트 템플릿
    GENRE_PROMPTS = {
        "technology": (
            "A {style} book cover for a technology book. "
            "Clean, futuristic design with subtle digital circuit patterns and cool-toned gradients. "
        ),
        "business": (
            "A {style} book cover for a business book. "
            "Sophisticated, corporate feel with geometric shapes and warm gold or navy tones. "
        ),
        "fiction": (
            "A {style} book cover for a fiction novel. "
            "Dramatic, cinematic composition with moody lighting and rich colours. "
        ),
        "self-help": (
            "A {style} book cover for a self-help and motivation book. "
            "Bright, inspiring design with sunrise or nature imagery and uplifting energy. "
        ),
        "science": (
            "A {style} book cover for a science book. "
            "Visually striking design with macro-photography style scientific imagery. "
        ),
    }
    
    DEFAULT_TEMPLATE = (
        "A {style} professional book cover. "
        "Clean, modern design suitable for Amazon KDP publishing. "
    )
    
    def __init__(
        self,
        image_backend: ImageBackend,
        progress_callback: Optional[Callable[[str], None]] = None,
    ):
        self.image_backend = image_backend
        self.progress_callback = progress_callback or print
    
    def _log(self, message: str):
        """진행 상황 출력"""
        self.progress_callback(message)
    
    def build_prompt(self, config: BookConfig) -> str:
        """표지 생성 프롬프트 구성"""
        genre = config.genre.lower()
        style = config.cover.style
        title = config.title
        
        template = self.GENRE_PROMPTS.get(genre, self.DEFAULT_TEMPLATE)
        base = template.format(style=style)
        
        return (
            f"{base}"
            f"The words '{title}' should appear prominently on the cover in a clean readable font. "
            f"Professional publishing quality, high resolution, no watermarks."
        )
    
    def generate_cover(self, config: BookConfig, output_dir: Path) -> Path:
        """표지 이미지 생성"""
        self._log("🎨 표지 이미지 생성 중...")
        
        prompt = self.build_prompt(config)
        
        # 이미지 생성
        image_bytes = self.image_backend.generate(prompt, size=(1024, 1024))
        
        # 파일 저장
        output_dir.mkdir(parents=True, exist_ok=True)
        cover_path = output_dir / "cover.png"
        cover_path.write_bytes(image_bytes)
        
        self._log(f"✅ 표지 저장 완료: {cover_path}")
        
        return cover_path
