"""
콘텐츠 생성기
LLM을 사용하여 책 본문을 생성
"""

import re
from pathlib import Path
from typing import Callable, Optional

from .config import BookConfig
from .backends import LLMBackend


class ContentGenerator:
    """책 콘텐츠 생성기"""
    
    def __init__(
        self,
        llm: LLMBackend,
        progress_callback: Optional[Callable[[str], None]] = None,
    ):
        self.llm = llm
        self.progress_callback = progress_callback or print
    
    def _log(self, message: str):
        """진행 상황 출력"""
        self.progress_callback(message)
    
    def generate_outline(self, config: BookConfig) -> str:
        """목차 자동 생성"""
        self._log("📝 목차 생성 중...")
        
        system_prompt = f"You are a professional book outliner. Always respond in {config.language}."
        
        prompt = f"""다음 책의 상세 목차를 작성해주세요.
제목: {config.title}
주제: {config.topic}

12~15개 챕터를 작성하고, 각 챕터에 세부 소제목 2~3개를 포함시켜주세요.
형식: '1. 챕터 제목'"""
        
        outline = self.llm.generate(prompt, system_prompt)
        self._log("✅ 목차 생성 완료")
        return outline
    
    def parse_chapters(self, outline: str) -> list[str]:
        """목차 텍스트에서 챕터 제목 리스트 추출"""
        chapters = []
        
        for line in outline.split("\n"):
            line = line.strip()
            if not line:
                continue
            
            # "1. 제목", "1) 제목", "Chapter 1" 등 다양한 패턴 매칭
            for i in range(1, 25):
                if line.startswith(f"{i}.") or line.startswith(f"{i})"):
                    # 숫자와 구분자 제거
                    title = re.sub(r"^\d+[\.\)]\s*", "", line).strip()
                    if title:
                        chapters.append(title)
                    break
        
        # 챕터가 없으면 기본값
        if not chapters:
            chapters = ["개론", "본론", "결론"]
        
        return chapters

    
    def generate_chapter(
        self,
        config: BookConfig,
        chapter_title: str,
        chapter_num: int,
    ) -> str:
        """단일 챕터 생성"""
        system_prompt = (
            f"You are a professional author writing a book in {config.language}. "
            f"Write detailed, engaging, and informative chapters with clear structure."
        )
        
        prompt = f"""책 제목: {config.title}
전체 주제: {config.topic}
현재 챕터: Chapter {chapter_num} — {chapter_title}

이 챕터를 1500~2000자 정도로 작성해주세요.
### 소제목을 3개 이상 사용하여 구조를 잡고, 실제 사례와 설명을 포함시켜주세요."""
        
        content = self.llm.generate(prompt, system_prompt)
        return f"## Chapter {chapter_num}: {chapter_title}\n\n{content}"
    
    def generate_book(self, config: BookConfig, output_dir: Path) -> str:
        """전체 책 생성"""
        # 목차 준비
        outline = config.outline.strip()
        if not outline:
            outline = self.generate_outline(config)
        
        chapters = self.parse_chapters(outline)
        total_chapters = len(chapters)
        
        self._log(f"📚 총 {total_chapters}개 챕터 생성 시작")
        
        # 책 제목
        lines = [f"# {config.title}\n"]
        
        # 챕터별 생성
        for idx, chapter_title in enumerate(chapters, 1):
            self._log(f"📖 Chapter {idx}/{total_chapters} 생성 중: {chapter_title}")
            
            chapter_md = self.generate_chapter(config, chapter_title, idx)
            lines.append(chapter_md)
        
        content = "\n\n".join(lines)
        
        # 파일 저장
        output_dir.mkdir(parents=True, exist_ok=True)
        manuscript_path = output_dir / "manuscript.md"
        manuscript_path.write_text(content, encoding="utf-8")
        
        self._log(f"✅ 원고 저장 완료: {manuscript_path}")
        
        return content
