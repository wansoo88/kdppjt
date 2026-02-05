"""
비용 추적기
API 사용량 및 비용 추적
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


# 백엔드별 가격 정책 (USD per 1M tokens)
PRICING = {
    "claude/claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
    "claude/claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
    "claude/claude-3-sonnet-20240229": {"input": 3.0, "output": 15.0},
    "claude/claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
    "ollama": {"input": 0.0, "output": 0.0},  # 무료
}


@dataclass
class CostRecord:
    """비용 기록"""
    backend: str
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "backend": self.backend,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "estimated_cost_usd": round(self.estimated_cost, 6),
        }


class CostTracker:
    """비용 추적기"""
    
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path("output")
        self.records: Dict[str, CostRecord] = {}
    
    def record(self, backend_name: str, input_tokens: int, output_tokens: int):
        """토큰 사용량 기록"""
        if backend_name not in self.records:
            self.records[backend_name] = CostRecord(backend=backend_name)
        
        record = self.records[backend_name]
        record.input_tokens += input_tokens
        record.output_tokens += output_tokens
        
        # 비용 계산
        pricing = self._get_pricing(backend_name)
        input_cost = (record.input_tokens / 1_000_000) * pricing["input"]
        output_cost = (record.output_tokens / 1_000_000) * pricing["output"]
        record.estimated_cost = input_cost + output_cost
    
    def _get_pricing(self, backend_name: str) -> dict:
        """백엔드별 가격 정책 조회"""
        # 정확한 매칭
        if backend_name in PRICING:
            return PRICING[backend_name]
        
        # ollama로 시작하면 무료
        if backend_name.startswith("ollama"):
            return PRICING["ollama"]
        
        # claude로 시작하면 기본 sonnet 가격
        if backend_name.startswith("claude"):
            return PRICING["claude/claude-3-5-sonnet-20241022"]
        
        # 기본값
        return {"input": 0.0, "output": 0.0}
    
    def get_total_cost(self) -> float:
        """총 비용 계산"""
        return sum(r.estimated_cost for r in self.records.values())
    
    def get_summary(self) -> dict:
        """비용 요약"""
        return {
            "records": {k: v.to_dict() for k, v in self.records.items()},
            "total_cost_usd": round(self.get_total_cost(), 6),
        }
    
    def save_summary(self):
        """비용 요약 저장"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        summary_path = self.output_dir / "cost_summary.json"
        
        # 기존 데이터 로드 및 병합
        existing = {}
        if summary_path.exists():
            try:
                existing = json.loads(summary_path.read_text(encoding="utf-8"))
            except:
                pass
        
        # 현재 세션 추가
        current = self.get_summary()
        
        # 누적 비용 계산
        cumulative_cost = existing.get("cumulative_cost_usd", 0.0) + current["total_cost_usd"]
        
        data = {
            "last_session": current,
            "cumulative_cost_usd": round(cumulative_cost, 6),
        }
        
        summary_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        return summary_path
