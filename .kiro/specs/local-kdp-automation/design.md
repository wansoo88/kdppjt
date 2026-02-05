# Design Document: Local KDP Automation

## Overview

로컬 환경에서 실행되는 KDP 자동화 파이프라인입니다. AWS 의존성을 완전히 제거하고, Ollama(무료) 또는 Claude API를 통한 텍스트 생성과 Stable Diffusion을 통한 이미지 생성을 지원합니다.

### 핵심 설계 원칙

1. **플러그인 아키텍처**: LLM 백엔드를 쉽게 교체할 수 있는 추상화 레이어
2. **단계별 실행**: 각 단계가 독립적으로 실행되어 실패 시 재개 가능
3. **로컬 우선**: 모든 데이터는 로컬 파일 시스템에 저장
4. **설정 기반**: YAML 설정 파일로 모든 옵션 제어

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI (run.py)                         │
│                    python run.py --config                   │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                      Pipeline Orchestrator                   │
│                     (kdp/pipeline.py)                        │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────────┐ │
│  │ Config  │→ │ Content │→ │  Cover  │→ │  PDF Assembler  │ │
│  │ Loader  │  │Generator│  │Designer │  │                 │ │
│  └─────────┘  └────┬────┘  └────┬────┘  └────────┬────────┘ │
└────────────────────┼────────────┼────────────────┼──────────┘
                     │            │                │
        ┌────────────▼────┐  ┌────▼─────┐    ┌────▼─────┐
        │   LLM Backend   │  │  Image   │    │   FPDF   │
        │  ┌──────────┐   │  │ Backend  │    │  Library │
        │  │  Ollama  │   │  │┌────────┐│    └──────────┘
        │  └──────────┘   │  ││Stable  ││
        │  ┌──────────┐   │  ││Diffusion│
        │  │  Claude  │   │  │└────────┘│
        │  └──────────┘   │  └──────────┘
        └─────────────────┘
```

## Components and Interfaces

### 1. BookConfig (데이터 모델)

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class CoverConfig:
    style: str = "modern minimalist"

@dataclass
class Metadata:
    description: str = ""
    keywords: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    price: str = "9.99"

@dataclass
class BookConfig:
    id: str
    title: str
    author: str
    topic: str
    genre: str = "general"
    language: str = "ko"
    llm_backend: str = "ollama"  # ollama | claude
    cover: CoverConfig = field(default_factory=CoverConfig)
    metadata: Metadata = field(default_factory=Metadata)
    outline: str = ""
```

### 2. LLM Backend Interface

```python
from abc import ABC, abstractmethod

class LLMBackend(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """텍스트 생성"""
        pass
    
    @abstractmethod
    def get_token_usage(self) -> dict:
        """토큰 사용량 반환"""
        pass

class OllamaBackend(LLMBackend):
    def __init__(self, model: str = "llama3.1", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
    
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        # Ollama API 호출
        pass

class ClaudeBackend(LLMBackend):
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key
        self.model = model
    
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        # Anthropic API 호출
        pass
```

### 3. Image Backend Interface

```python
class ImageBackend(ABC):
    @abstractmethod
    def generate(self, prompt: str, size: tuple = (1024, 1024)) -> bytes:
        """이미지 생성"""
        pass

class StableDiffusionBackend(ImageBackend):
    def __init__(self, base_url: str = "http://localhost:7860"):
        self.base_url = base_url
    
    def generate(self, prompt: str, size: tuple = (1024, 1024)) -> bytes:
        # Stable Diffusion WebUI API 호출
        pass
```

### 4. Content Generator

```python
class ContentGenerator:
    def __init__(self, llm: LLMBackend):
        self.llm = llm
    
    def generate_outline(self, config: BookConfig) -> str:
        """목차 자동 생성"""
        pass
    
    def generate_chapter(self, config: BookConfig, chapter_title: str, chapter_num: int) -> str:
        """단일 챕터 생성"""
        pass
    
    def generate_book(self, config: BookConfig) -> str:
        """전체 책 생성"""
        pass
```

### 5. Cover Designer

```python
class CoverDesigner:
    GENRE_PROMPTS = {
        "technology": "futuristic, digital circuits, cool gradients",
        "business": "corporate, geometric, gold and navy",
        "fiction": "dramatic, cinematic, moody lighting",
        "self-help": "bright, inspiring, sunrise imagery",
        "science": "scientific imagery, macro photography",
    }
    
    def __init__(self, image_backend: ImageBackend):
        self.image_backend = image_backend
    
    def generate_cover(self, config: BookConfig) -> bytes:
        """표지 이미지 생성"""
        pass
```

### 6. PDF Assembler

```python
class PDFAssembler:
    def __init__(self):
        self.font_loaded = False
    
    def build_interior(self, config: BookConfig, content: str) -> str:
        """본문 PDF 생성, 파일 경로 반환"""
        pass
    
    def build_cover(self, cover_image_path: str) -> str:
        """표지 PDF 생성, 파일 경로 반환"""
        pass
```

### 7. Pipeline Orchestrator

```python
class Pipeline:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.status = PipelineStatus()
    
    def run(self, resume: bool = False) -> dict:
        """전체 파이프라인 실행"""
        pass
    
    def _save_status(self):
        """상태 저장"""
        pass
```

## Data Models

### PipelineStatus

```python
@dataclass
class PipelineStatus:
    content_generated: bool = False
    cover_generated: bool = False
    pdf_assembled: bool = False
    completed: bool = False
    error: Optional[str] = None
    token_usage: dict = field(default_factory=dict)
    estimated_cost: float = 0.0
```

### Manifest

```python
@dataclass
class Manifest:
    book_id: str
    title: str
    author: str
    files: dict  # {manuscript, cover, interior_pdf, cover_pdf}
    metadata: dict
    ai_generated: bool = True
    quality_check: dict = field(default_factory=dict)
    cost: dict = field(default_factory=dict)
    created_at: str = ""
```

## File Structure

```
kdppjt/
├── run.py                    # CLI 진입점
├── kdp/
│   ├── __init__.py
│   ├── config.py             # BookConfig, 설정 로더
│   ├── pipeline.py           # Pipeline Orchestrator
│   ├── content_generator.py  # 콘텐츠 생성
│   ├── cover_designer.py     # 표지 디자인
│   ├── pdf_assembler.py      # PDF 조립
│   ├── quality_checker.py    # 품질 검증
│   └── backends/
│       ├── __init__.py
│       ├── llm_base.py       # LLM 추상 클래스
│       ├── ollama.py         # Ollama 백엔드
│       ├── claude.py         # Claude 백엔드
│       ├── image_base.py     # Image 추상 클래스
│       └── stable_diffusion.py
├── config/
│   └── book_config.yaml      # 샘플 설정
├── output/                   # 생성된 파일들
│   └── <book_id>/
│       ├── manuscript.md
│       ├── cover.png
│       ├── interior.pdf
│       ├── cover.pdf
│       ├── manifest.json
│       └── status.json
├── fonts/                    # 한국어 폰트
│   └── NotoSansKR-Regular.otf
├── .env.example
└── requirements.txt
```



## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: 설정 파싱 유효성 (Config Parsing Validity)

*For any* 유효한 YAML 설정 파일, 파싱 후 생성된 BookConfig 객체는 원본 YAML의 모든 필드 값을 정확히 반영해야 한다.

**Validates: Requirements 1.1, 1.2**

### Property 2: 필수 필드 검증 (Required Field Validation)

*For any* 설정 파일에서 필수 필드(title, author, topic) 중 하나라도 누락되면, 파이프라인은 ValidationError를 발생시켜야 한다.

**Validates: Requirements 1.2**

### Property 3: 목차 파싱 정확성 (Outline Parsing Accuracy)

*For any* 유효한 목차 문자열, 파싱 결과는 원본의 모든 챕터 제목을 순서대로 포함해야 한다.

**Validates: Requirements 2.5**

### Property 4: 프롬프트 생성 정확성 (Prompt Generation Accuracy)

*For any* BookConfig, 생성된 표지 프롬프트는 반드시 책 제목을 포함하고, 장르에 해당하는 스타일 키워드를 포함해야 한다.

**Validates: Requirements 3.3, 3.6**

### Property 5: 마크다운 헤딩 변환 (Markdown Heading Conversion)

*For any* 마크다운 문서, ## 헤딩은 챕터 제목으로, ### 헤딩은 소제목으로 변환되어야 한다.

**Validates: Requirements 4.4**

### Property 6: 출력 디렉토리 구조 (Output Directory Structure)

*For any* book_id, 출력 디렉토리 경로는 항상 `output/{book_id}/` 형식이어야 한다.

**Validates: Requirements 5.6**

### Property 7: LLM 백엔드 선택 (LLM Backend Selection)

*For any* 설정 파일의 llm_backend 값, 파이프라인은 해당하는 올바른 백엔드 인스턴스를 생성해야 한다.

**Validates: Requirements 6.3**

### Property 8: 상태 파일 일관성 (Status File Consistency)

*For any* 파이프라인 실행, status.json은 각 단계의 완료 상태를 정확히 반영해야 한다.

**Validates: Requirements 7.4**

### Property 9: 품질 검증 정확성 (Quality Check Accuracy)

*For any* 생성된 콘텐츠, 품질 검증기는 정확한 단어 수, 챕터 수, 중복 문장 비율을 계산해야 한다.

**Validates: Requirements 8.1, 8.2, 8.3**

### Property 10: Manifest 구조 완전성 (Manifest Structure Completeness)

*For any* 완료된 파이프라인 실행, manifest.json은 ai_generated 필드, 품질 검증 결과, 예상 비용을 포함해야 한다.

**Validates: Requirements 5.4, 8.5, 8.6, 9.2**

### Property 11: 비용 계산 정확성 (Cost Calculation Accuracy)

*For any* 토큰 사용량, 예상 비용은 해당 백엔드의 가격 정책에 따라 정확히 계산되어야 한다.

**Validates: Requirements 9.2**

## Error Handling

### 설정 오류
- `ConfigNotFoundError`: 설정 파일이 존재하지 않을 때
- `ConfigValidationError`: 필수 필드 누락 또는 잘못된 값

### API 오류
- `LLMConnectionError`: LLM 백엔드 연결 실패
- `LLMGenerationError`: 텍스트 생성 실패 (재시도 후)
- `ImageGenerationError`: 이미지 생성 실패

### 파일 시스템 오류
- `OutputDirectoryError`: 출력 디렉토리 생성 실패
- `FontDownloadError`: 폰트 다운로드 실패 (폴백 사용)

### 재시도 정책
```python
RETRY_CONFIG = {
    "max_retries": 3,
    "base_delay": 1.0,  # seconds
    "max_delay": 30.0,
    "exponential_base": 2,
}
```

## Testing Strategy

### 단위 테스트 (Unit Tests)
- 설정 파싱 및 검증
- 목차 파싱 로직
- 프롬프트 생성 로직
- 품질 검증 알고리즘
- 비용 계산 로직

### 속성 기반 테스트 (Property-Based Tests)
- **라이브러리**: `hypothesis` (Python)
- **최소 반복 횟수**: 100회
- 각 속성에 대해 무작위 입력으로 테스트

### 통합 테스트
- Mock 백엔드를 사용한 전체 파이프라인 테스트
- 재개 기능 테스트
- 오류 복구 테스트

### 테스트 구조
```
tests/
├── unit/
│   ├── test_config.py
│   ├── test_content_generator.py
│   ├── test_cover_designer.py
│   ├── test_pdf_assembler.py
│   └── test_quality_checker.py
├── property/
│   ├── test_config_properties.py
│   ├── test_prompt_properties.py
│   └── test_quality_properties.py
└── integration/
    └── test_pipeline.py
```
