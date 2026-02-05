"""
설정 관리 모듈
YAML 설정 파일 파싱 및 BookConfig 데이터 클래스
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import yaml


class ConfigError(Exception):
    """설정 관련 오류 기본 클래스"""
    pass


class ConfigNotFoundError(ConfigError):
    """설정 파일을 찾을 수 없을 때"""
    pass


class ConfigValidationError(ConfigError):
    """설정 검증 실패"""
    pass


@dataclass
class CoverConfig:
    """표지 설정"""
    style: str = "modern minimalist"


@dataclass
class Metadata:
    """책 메타데이터"""
    description: str = ""
    keywords: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    price: str = "9.99"


@dataclass
class BookConfig:
    """책 설정 데이터 클래스"""
    id: str
    title: str
    author: str
    topic: str
    genre: str = "general"
    language: str = "ko"
    llm_backend: str = "ollama"  # ollama | claude | mock
    image_backend: str = "stable_diffusion"  # stable_diffusion | mock
    cover: CoverConfig = field(default_factory=CoverConfig)
    metadata: Metadata = field(default_factory=Metadata)
    outline: str = ""


    @classmethod
    def from_dict(cls, data: dict) -> "BookConfig":
        """딕셔너리에서 BookConfig 생성"""
        book_data = data.get("book", data)
        
        # 필수 필드 검증
        required_fields = ["title", "author", "topic"]
        missing = [f for f in required_fields if not book_data.get(f)]
        if missing:
            raise ConfigValidationError(
                f"필수 필드가 누락되었습니다: {', '.join(missing)}"
            )
        
        # CoverConfig 파싱
        cover_data = book_data.get("cover", {})
        cover = CoverConfig(
            style=cover_data.get("style", "modern minimalist")
        )
        
        # Metadata 파싱
        meta_data = book_data.get("metadata", {})
        metadata = Metadata(
            description=meta_data.get("description", ""),
            keywords=meta_data.get("keywords", []),
            categories=meta_data.get("categories", []),
            price=str(meta_data.get("price", "9.99")),
        )
        
        return cls(
            id=book_data.get("id", "book-001"),
            title=book_data["title"],
            author=book_data["author"],
            topic=book_data["topic"],
            genre=book_data.get("genre", "general"),
            language=book_data.get("language", "ko"),
            llm_backend=book_data.get("llm_backend", "ollama"),
            image_backend=book_data.get("image_backend", "stable_diffusion"),
            cover=cover,
            metadata=metadata,
            outline=book_data.get("outline", ""),
        )


def load_config(config_path: str | Path) -> BookConfig:
    """YAML 설정 파일 로드"""
    path = Path(config_path)
    
    if not path.exists():
        raise ConfigNotFoundError(
            f"설정 파일을 찾을 수 없습니다: {path.absolute()}"
        )
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigValidationError(f"YAML 파싱 오류: {e}")
    
    if not data:
        raise ConfigValidationError("설정 파일이 비어있습니다")
    
    return BookConfig.from_dict(data)
