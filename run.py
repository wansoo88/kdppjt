#!/usr/bin/env python3
"""
KDP Local Automation CLI
책 생성 파이프라인 실행

사용법:
    python run.py --config config/book_config.yaml
    python run.py --config config/book_config.yaml --resume
    python run.py --config config/book_config.yaml --mock  # 테스트 모드
"""

import argparse
import sys
from pathlib import Path

# .env 파일 로드
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from kdp.pipeline import Pipeline
from kdp.config import ConfigError, load_config


def main():
    parser = argparse.ArgumentParser(
        description="KDP Local Automation - AI 기반 책 자동 생성",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
    python run.py --config config/book_config.yaml
    python run.py --config config/book_config.yaml --resume
    python run.py --config config/book_config.yaml --mock

환경 변수:
    ANTHROPIC_API_KEY   Claude API 키 (claude 백엔드 사용 시)
    OLLAMA_BASE_URL     Ollama 서버 URL (기본: http://localhost:11434)
    SD_BASE_URL         Stable Diffusion WebUI URL (기본: http://localhost:7860)
        """
    )
    
    parser.add_argument(
        "--config", "-c",
        required=True,
        help="책 설정 YAML 파일 경로"
    )
    
    parser.add_argument(
        "--resume", "-r",
        action="store_true",
        help="이전 실행에서 재개"
    )
    
    parser.add_argument(
        "--mock", "-m",
        action="store_true",
        help="Mock 백엔드로 테스트 실행 (외부 서비스 불필요)"
    )
    
    args = parser.parse_args()
    
    # 설정 파일 존재 확인
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"❌ 설정 파일을 찾을 수 없습니다: {config_path}")
        sys.exit(1)
    
    try:
        # Mock 모드일 경우 설정 오버라이드
        if args.mock:
            print("🧪 Mock 모드로 실행 (테스트용)")
            # 임시로 설정 파일을 수정하지 않고 Pipeline에서 처리
        
        pipeline = Pipeline(str(config_path), mock_mode=args.mock)
        result = pipeline.run(resume=args.resume)
        
        if result["success"]:
            print("\n🎉 책 생성 완료!")
            print(f"📁 출력 위치: {result['output_dir']}")
            sys.exit(0)
        else:
            sys.exit(1)
            
    except ConfigError as e:
        print(f"❌ 설정 오류: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ 사용자에 의해 중단됨")
        sys.exit(130)
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
