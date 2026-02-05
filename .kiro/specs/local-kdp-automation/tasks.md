# Implementation Plan: Local KDP Automation

## Overview

AWS 의존성을 제거한 로컬 KDP 자동화 파이프라인 구현. Ollama/Claude 백엔드와 Stable Diffusion을 활용한 완전 무료 옵션 지원.

## Tasks

- [x] 1. 프로젝트 구조 설정 및 기본 인터페이스 정의
  - [x] 1.1 새로운 kdp/ 패키지 디렉토리 구조 생성
    - kdp/, kdp/backends/ 디렉토리 생성
    - __init__.py 파일들 생성
    - _Requirements: 5.6_
  - [x] 1.2 requirements.txt 업데이트
    - fpdf2, pyyaml, python-dotenv, requests, anthropic, hypothesis 추가
    - _Requirements: 2.2, 3.2_
  - [x] 1.3 .env.example 파일 생성
    - ANTHROPIC_API_KEY, OLLAMA_BASE_URL, SD_BASE_URL 템플릿
    - _Requirements: 6.1, 6.2_

- [x] 2. 설정 관리 모듈 구현
  - [x] 2.1 BookConfig 데이터 클래스 구현 (kdp/config.py)
    - BookConfig, CoverConfig, Metadata 데이터 클래스
    - YAML 로더 함수
    - 필수 필드 검증 로직
    - _Requirements: 1.1, 1.2, 1.3, 1.4_
  - [ ]* 2.2 설정 파싱 속성 테스트 작성
    - **Property 1: 설정 파싱 유효성**
    - **Property 2: 필수 필드 검증**
    - **Validates: Requirements 1.1, 1.2**

- [x] 3. LLM 백엔드 구현
  - [x] 3.1 LLM 추상 클래스 정의 (kdp/backends/llm_base.py)
    - LLMBackend ABC 클래스
    - generate(), get_token_usage() 메서드
    - _Requirements: 2.1, 2.2_
  - [x] 3.2 Ollama 백엔드 구현 (kdp/backends/ollama.py)
    - OllamaBackend 클래스
    - localhost:11434 연결
    - _Requirements: 2.3_
  - [x] 3.3 Claude 백엔드 구현 (kdp/backends/claude.py)
    - ClaudeBackend 클래스
    - Anthropic API 호출
    - 토큰 사용량 추적
    - _Requirements: 2.4, 9.1_
  - [x] 3.4 백엔드 팩토리 함수 구현
    - llm_backend 설정값에 따른 인스턴스 생성
    - _Requirements: 6.3_
  - [ ]* 3.5 LLM 백엔드 선택 속성 테스트 작성
    - **Property 7: LLM 백엔드 선택**
    - **Validates: Requirements 6.3**

- [x] 4. Checkpoint - 백엔드 기본 구조 검증
  - 모든 테스트 통과 확인, 질문 있으면 사용자에게 문의

- [x] 5. 콘텐츠 생성기 구현
  - [x] 5.1 ContentGenerator 클래스 구현 (kdp/content_generator.py)
    - 목차 파싱 로직 (_parse_chapters)
    - 목차 자동 생성 (generate_outline)
    - 챕터별 콘텐츠 생성 (generate_chapter)
    - 전체 책 생성 (generate_book)
    - 진행 상황 출력
    - _Requirements: 2.5, 2.6, 2.7, 2.8, 2.9, 1.5_
  - [ ]* 5.2 목차 파싱 속성 테스트 작성
    - **Property 3: 목차 파싱 정확성**
    - **Validates: Requirements 2.5**

- [x] 6. 이미지 백엔드 및 표지 디자이너 구현
  - [x] 6.1 이미지 백엔드 추상 클래스 정의 (kdp/backends/image_base.py)
    - ImageBackend ABC 클래스
    - _Requirements: 3.1_
  - [x] 6.2 Stable Diffusion 백엔드 구현 (kdp/backends/stable_diffusion.py)
    - StableDiffusionBackend 클래스
    - WebUI API 호출 (localhost:7860)
    - _Requirements: 3.2_
  - [x] 6.3 CoverDesigner 클래스 구현 (kdp/cover_designer.py)
    - 장르별 프롬프트 템플릿
    - 프롬프트 생성 로직
    - 이미지 저장
    - _Requirements: 3.3, 3.4, 3.5, 3.6_
  - [ ]* 6.4 프롬프트 생성 속성 테스트 작성
    - **Property 4: 프롬프트 생성 정확성**
    - **Validates: Requirements 3.3, 3.6**

- [x] 7. PDF 조립기 구현
  - [x] 7.1 PDFAssembler 클래스 구현 (kdp/pdf_assembler.py)
    - 한국어 폰트 다운로드/캐싱
    - 마크다운 → PDF 변환
    - 타이틀 페이지, 헤더, 푸터
    - 본문 PDF 생성 (build_interior)
    - 표지 PDF 생성 (build_cover)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_
  - [ ]* 7.2 마크다운 헤딩 변환 속성 테스트 작성
    - **Property 5: 마크다운 헤딩 변환**
    - **Validates: Requirements 4.4**

- [x] 8. Checkpoint - 핵심 모듈 검증
  - 모든 테스트 통과 확인, 질문 있으면 사용자에게 문의

- [x] 9. 품질 검증기 구현
  - [x] 9.1 QualityChecker 클래스 구현 (kdp/quality_checker.py)
    - 단어 수 계산
    - 챕터 수 계산
    - 중복 문장 비율 계산
    - 품질 검증 결과 반환
    - _Requirements: 8.1, 8.2, 8.3, 8.4_
  - [ ]* 9.2 품질 검증 속성 테스트 작성
    - **Property 9: 품질 검증 정확성**
    - **Validates: Requirements 8.1, 8.2, 8.3**

- [x] 10. 비용 추적기 구현
  - [x] 10.1 CostTracker 클래스 구현 (kdp/cost_tracker.py)
    - 토큰 사용량 기록
    - 백엔드별 비용 계산
    - 누적 비용 저장/로드
    - _Requirements: 9.1, 9.2, 9.4_
  - [ ]* 10.2 비용 계산 속성 테스트 작성
    - **Property 11: 비용 계산 정확성**
    - **Validates: Requirements 9.2**

- [x] 11. 파이프라인 오케스트레이터 구현
  - [x] 11.1 Pipeline 클래스 구현 (kdp/pipeline.py)
    - 설정 로드
    - 단계별 실행 (콘텐츠 → 표지 → PDF)
    - 상태 저장/로드 (status.json)
    - 재개 기능 (--resume)
    - manifest.json 생성
    - 오류 처리 및 복구
    - _Requirements: 5.2, 5.3, 5.4, 5.5, 7.1, 7.2, 7.3, 7.4_
  - [ ]* 11.2 상태 파일 및 출력 디렉토리 속성 테스트 작성
    - **Property 6: 출력 디렉토리 구조**
    - **Property 8: 상태 파일 일관성**
    - **Property 10: Manifest 구조 완전성**
    - **Validates: Requirements 5.4, 5.6, 7.4, 8.5, 8.6, 9.2**

- [x] 12. CLI 진입점 구현
  - [x] 12.1 run.py CLI 구현
    - argparse로 --config, --resume 옵션 처리
    - 환경 변수 및 .env 로드
    - 파이프라인 실행
    - 결과 출력
    - _Requirements: 5.1, 6.1, 6.2, 6.4, 6.5, 6.6_

- [x] 13. 샘플 설정 파일 업데이트
  - [x] 13.1 config/book_config.yaml 업데이트
    - llm_backend 필드 추가
    - 새로운 구조에 맞게 수정
    - _Requirements: 1.4_

- [x] 14. Final Checkpoint - 전체 시스템 검증
  - 모든 테스트 통과 확인
  - 전체 파이프라인 수동 테스트
  - 질문 있으면 사용자에게 문의

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- MVP는 Ollama + Stable Diffusion 무료 옵션으로 먼저 구현
