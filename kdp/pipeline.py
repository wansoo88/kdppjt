"""
파이프라인 오케스트레이터
전체 책 생성 파이프라인 관리
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from .config import BookConfig, load_config
from .backends import create_llm_backend, create_image_backend
from .content_generator import ContentGenerator
from .cover_designer import CoverDesigner
from .pdf_assembler import PDFAssembler
from .quality_checker import QualityChecker
from .cost_tracker import CostTracker


@dataclass
class PipelineStatus:
    """파이프라인 상태"""
    content_generated: bool = False
    cover_generated: bool = False
    pdf_assembled: bool = False
    completed: bool = False
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "content_generated": self.content_generated,
            "cover_generated": self.cover_generated,
            "pdf_assembled": self.pdf_assembled,
            "completed": self.completed,
            "error": self.error,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "PipelineStatus":
        return cls(
            content_generated=data.get("content_generated", False),
            cover_generated=data.get("cover_generated", False),
            pdf_assembled=data.get("pdf_assembled", False),
            completed=data.get("completed", False),
            error=data.get("error"),
        )


class Pipeline:
    """책 생성 파이프라인"""
    
    def __init__(
        self,
        config_path: str,
        progress_callback: Optional[Callable[[str], None]] = None,
        mock_mode: bool = False,
    ):
        self.config_path = Path(config_path)
        self.progress_callback = progress_callback or print
        self.mock_mode = mock_mode
        self.config: Optional[BookConfig] = None
        self.output_dir: Optional[Path] = None
        self.status = PipelineStatus()
        self.cost_tracker: Optional[CostTracker] = None
    
    def _log(self, message: str):
        """진행 상황 출력"""
        self.progress_callback(message)

    
    def _load_status(self) -> PipelineStatus:
        """상태 파일 로드"""
        status_path = self.output_dir / "status.json"
        if status_path.exists():
            try:
                data = json.loads(status_path.read_text(encoding="utf-8"))
                return PipelineStatus.from_dict(data)
            except:
                pass
        return PipelineStatus()
    
    def _save_status(self):
        """상태 파일 저장"""
        status_path = self.output_dir / "status.json"
        status_path.write_text(
            json.dumps(self.status.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    
    def _save_manifest(self, quality_result=None):
        """매니페스트 저장"""
        manifest = {
            "book_id": self.config.id,
            "title": self.config.title,
            "author": self.config.author,
            "files": {
                "manuscript": str(self.output_dir / "manuscript.md"),
                "cover": str(self.output_dir / "cover.png"),
                "interior_pdf": str(self.output_dir / "interior.pdf"),
                "cover_pdf": str(self.output_dir / "cover.pdf"),
            },
            "metadata": {
                "description": self.config.metadata.description,
                "keywords": self.config.metadata.keywords,
                "categories": self.config.metadata.categories,
                "price_usd": self.config.metadata.price,
                "language": self.config.language,
            },
            "ai_generated": True,
            "quality_check": quality_result.to_dict() if quality_result else {},
            "cost": self.cost_tracker.get_summary() if self.cost_tracker else {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        manifest_path = self.output_dir / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        return manifest_path
    
    def run(self, resume: bool = False) -> dict:
        """파이프라인 실행"""
        self._log("🚀 KDP 파이프라인 시작")
        
        # 설정 로드
        self._log(f"📂 설정 파일 로드: {self.config_path}")
        self.config = load_config(self.config_path)
        
        # 출력 디렉토리 설정
        self.output_dir = Path("output") / self.config.id
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 비용 추적기 초기화
        self.cost_tracker = CostTracker(Path("output"))
        
        # 재개 모드
        if resume:
            self.status = self._load_status()
            self._log("🔄 이전 상태에서 재개")
        
        try:
            # 1. 콘텐츠 생성
            content = self._generate_content()
            
            # 2. 표지 생성
            cover_path = self._generate_cover()
            
            # 3. PDF 조립
            self._assemble_pdf(content, cover_path)
            
            # 4. 품질 검증
            quality_result = self._check_quality(content)
            
            # 5. 매니페스트 저장
            self._save_manifest(quality_result)
            
            # 완료
            self.status.completed = True
            self._save_status()
            
            # 비용 요약
            self.cost_tracker.save_summary()
            total_cost = self.cost_tracker.get_total_cost()
            
            self._log("=" * 50)
            self._log("✅ 파이프라인 완료!")
            self._log(f"📁 출력 디렉토리: {self.output_dir}")
            self._log(f"💰 예상 비용: ${total_cost:.4f}")
            self._log("=" * 50)
            
            return {
                "success": True,
                "output_dir": str(self.output_dir),
                "cost": total_cost,
            }
            
        except Exception as e:
            self.status.error = str(e)
            self._save_status()
            self._log(f"❌ 오류 발생: {e}")
            raise

    
    def _generate_content(self) -> str:
        """콘텐츠 생성 단계"""
        manuscript_path = self.output_dir / "manuscript.md"
        
        # 이미 생성된 경우 스킵
        if self.status.content_generated and manuscript_path.exists():
            self._log("⏭️ 콘텐츠 이미 생성됨, 스킵")
            return manuscript_path.read_text(encoding="utf-8")
        
        self._log("=" * 50)
        self._log("📝 1단계: 콘텐츠 생성")
        self._log("=" * 50)
        
        # LLM 백엔드 생성 (mock 모드면 mock 사용)
        backend_type = "mock" if self.mock_mode else self.config.llm_backend
        llm = create_llm_backend(backend_type)
        self._log(f"🤖 LLM 백엔드: {llm.name}")
        
        # 콘텐츠 생성
        generator = ContentGenerator(llm, self._log)
        content = generator.generate_book(self.config, self.output_dir)
        
        # 토큰 사용량 기록
        usage = llm.get_token_usage()
        self.cost_tracker.record(llm.name, usage["input_tokens"], usage["output_tokens"])
        
        self.status.content_generated = True
        self._save_status()
        
        return content
    
    def _generate_cover(self) -> Path:
        """표지 생성 단계"""
        cover_path = self.output_dir / "cover.png"
        
        # 이미 생성된 경우 스킵
        if self.status.cover_generated and cover_path.exists():
            self._log("⏭️ 표지 이미 생성됨, 스킵")
            return cover_path
        
        self._log("=" * 50)
        self._log("🎨 2단계: 표지 생성")
        self._log("=" * 50)
        
        # 이미지 백엔드 생성 (mock 모드면 mock 사용)
        backend_type = "mock" if self.mock_mode else self.config.image_backend
        image_backend = create_image_backend(backend_type)
        self._log(f"🖼️ 이미지 백엔드: {image_backend.name}")
        
        # 표지 생성
        designer = CoverDesigner(image_backend, self._log)
        cover_path = designer.generate_cover(self.config, self.output_dir)
        
        self.status.cover_generated = True
        self._save_status()
        
        return cover_path
    
    def _assemble_pdf(self, content: str, cover_path: Path):
        """PDF 조립 단계"""
        interior_path = self.output_dir / "interior.pdf"
        cover_pdf_path = self.output_dir / "cover.pdf"
        
        # 이미 생성된 경우 스킵
        if self.status.pdf_assembled and interior_path.exists() and cover_pdf_path.exists():
            self._log("⏭️ PDF 이미 생성됨, 스킵")
            return
        
        self._log("=" * 50)
        self._log("📄 3단계: PDF 조립")
        self._log("=" * 50)
        
        assembler = PDFAssembler(self._log)
        assembler.build_interior(self.config, content, self.output_dir)
        assembler.build_cover(cover_path, self.output_dir)
        
        self.status.pdf_assembled = True
        self._save_status()
    
    def _check_quality(self, content: str):
        """품질 검증 단계"""
        self._log("=" * 50)
        self._log("🔍 4단계: 품질 검증")
        self._log("=" * 50)
        
        checker = QualityChecker()
        result = checker.check(content)
        
        if result.passed:
            self._log("✅ 품질 검증 통과")
        else:
            self._log("⚠️ 품질 검증 경고:")
            for warning in result.warnings:
                self._log(f"   - {warning}")
        
        self._log(f"   단어 수: {result.word_count}")
        self._log(f"   챕터 수: {result.chapter_count}")
        self._log(f"   중복 비율: {result.duplicate_ratio:.1%}")
        
        return result
