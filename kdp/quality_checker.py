"""
품질 검증기
생성된 콘텐츠의 KDP 정책 준수 여부 검증
"""

import re
from dataclasses import dataclass
from typing import List


@dataclass
class QualityResult:
    """품질 검증 결과"""
    passed: bool
    word_count: int
    chapter_count: int
    duplicate_ratio: float
    warnings: List[str]
    
    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "word_count": self.word_count,
            "chapter_count": self.chapter_count,
            "duplicate_ratio": round(self.duplicate_ratio, 4),
            "warnings": self.warnings,
        }


class QualityChecker:
    """콘텐츠 품질 검증기"""
    
    def __init__(
        self,
        min_word_count: int = 10000,
        min_chapter_count: int = 5,
        max_duplicate_ratio: float = 0.15,
    ):
        self.min_word_count = min_word_count
        self.min_chapter_count = min_chapter_count
        self.max_duplicate_ratio = max_duplicate_ratio
    
    def count_words(self, content: str) -> int:
        """단어 수 계산 (한글 + 영문)"""
        # 한글: 공백으로 분리된 어절 수
        # 영문: 공백으로 분리된 단어 수
        words = content.split()
        return len(words)
    
    def count_chapters(self, content: str) -> int:
        """챕터 수 계산 (## 헤딩 기준)"""
        chapters = re.findall(r"^## ", content, re.MULTILINE)
        return len(chapters)
    
    def calculate_duplicate_ratio(self, content: str) -> float:
        """중복 문장 비율 계산"""
        # 문장 단위로 분리
        sentences = re.split(r"[.!?。]\s*", content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        if len(sentences) < 2:
            return 0.0
        
        # 중복 문장 찾기
        seen = set()
        duplicates = 0
        
        for sentence in sentences:
            # 정규화 (공백 제거, 소문자)
            normalized = re.sub(r"\s+", "", sentence.lower())
            if normalized in seen:
                duplicates += 1
            else:
                seen.add(normalized)
        
        return duplicates / len(sentences)
    
    def check(self, content: str) -> QualityResult:
        """품질 검증 실행"""
        warnings = []
        passed = True
        
        # 단어 수 검증
        word_count = self.count_words(content)
        if word_count < self.min_word_count:
            warnings.append(
                f"단어 수 부족: {word_count} (권장: {self.min_word_count}+)"
            )
            passed = False
        
        # 챕터 수 검증
        chapter_count = self.count_chapters(content)
        if chapter_count < self.min_chapter_count:
            warnings.append(
                f"챕터 수 부족: {chapter_count} (권장: {self.min_chapter_count}+)"
            )
            passed = False
        
        # 중복 비율 검증
        duplicate_ratio = self.calculate_duplicate_ratio(content)
        if duplicate_ratio > self.max_duplicate_ratio:
            warnings.append(
                f"중복 문장 비율 높음: {duplicate_ratio:.1%} (권장: {self.max_duplicate_ratio:.1%} 이하)"
            )
            passed = False
        
        return QualityResult(
            passed=passed,
            word_count=word_count,
            chapter_count=chapter_count,
            duplicate_ratio=duplicate_ratio,
            warnings=warnings,
        )
