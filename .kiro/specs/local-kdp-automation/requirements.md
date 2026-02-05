# Requirements Document

## Introduction

AWS 클라우드 의존성을 제거하고 로컬 환경에서 실행 가능한 KDP(Kindle Direct Publishing) 자동화 시스템입니다. Ollama(무료) 또는 Claude API(유료)를 활용하여 책 콘텐츠 생성, Stable Diffusion으로 표지 디자인, PDF 조립까지 자동화하며, 최종 결과물을 KDP에 수동 업로드할 수 있는 형태로 출력합니다.

### 전략적 방향

**초기 제품 전략: 니치 논픽션 전자책 자동화**

1. **타겟 시장**: 저경쟁 니치 키워드 기반 논픽션 (예: "홈 오피스 정리법", "미니멀리스트 재테크", "시니어 스마트폰 가이드")
2. **차별화 포인트**: 
   - 한국어 콘텐츠 특화 (경쟁 적음)
   - 빠른 출판 사이클 (아이디어 → 출판 24시간 이내)
   - 품질 검증 자동화 (맞춤법, 가독성 점수)
3. **수익 모델**: 
   - 월 10-20권 출판 목표
   - 권당 $2.99-$9.99 가격대
   - 로열티 70% (KDP Select)

**비용 구조 (완전 무료 옵션 제공):**

**Option A: 완전 무료 (로컬 AI) - MVP 권장**
- 텍스트 생성: Ollama + Llama 3.1/Mistral (로컬 실행, 무료)
- 이미지 생성: Stable Diffusion (로컬 실행, 무료)
- 요구사항: GPU 8GB+ VRAM 권장 (CPU도 가능하나 느림)
- 월 비용: $0

**Option B: Claude API (품질 우선 시)**
- 참고: Claude Pro 구독($20/월)과 Claude API는 별개 서비스
- Claude API는 console.anthropic.com에서 별도 가입 필요
- 신규 가입 시 $5 무료 크레딧 제공
- Claude 3.5 Sonnet: 입력 $3/백만토큰, 출력 $15/백만토큰
- 책 1권당 약 $0.5-2

**Option C: 하이브리드**
- 텍스트: Ollama (무료) 또는 Claude API (품질 우선 시)
- 이미지: Stable Diffusion (무료, 로컬)
- 월 비용: $0 ~ $40 (선택에 따라)

**MVP는 Option A (완전 무료)로 시작**
- Ollama + Stable Diffusion으로 무료 운영
- 품질 향상 필요 시 Claude API 추가 지원
- AWS Lambda, S3, Step Functions 비용 완전 제거

**KDP 정책 준수 전략:**
- AI 생성 콘텐츠는 KDP에서 허용됨 (2023년 9월 정책 업데이트)
- 단, 출판 시 "AI 생성 콘텐츠" 표시 필수 (KDP 업로드 시 체크박스)
- 품질 기준: 최소 10,000단어 이상, 중복 콘텐츠 금지
- 스팸 방지: 동일 주제 대량 출판 자제, 고유한 가치 제공 필수
- 저작권: AI가 생성한 콘텐츠는 저작권 문제 없음 (학습 데이터 기반 새 창작물)

**MVP 범위**:
- CLI 기반 단일 책 생성 파이프라인
- 로컬 파일 시스템 저장 (AWS 의존성 제거)
- YAML 설정 파일 기반 입력
- 환경변수 기반 API 키 관리

## Glossary

- **Pipeline**: 콘텐츠 생성부터 PDF 출력까지의 전체 자동화 흐름
- **Content_Generator**: Ollama(로컬, 무료) 또는 Claude API(유료)를 사용하여 책 본문을 생성하는 모듈
- **Cover_Designer**: Stable Diffusion(로컬, 무료)을 사용하여 책 표지 이미지를 생성하는 모듈
- **PDF_Assembler**: 마크다운 콘텐츠와 표지 이미지를 KDP 규격 PDF로 조립하는 모듈
- **Book_Config**: 책 메타데이터와 생성 옵션을 정의하는 YAML 설정 파일
- **Manuscript**: 생성된 책 본문 마크다운 파일
- **Interior_PDF**: KDP 본문용 PDF 파일
- **Cover_PDF**: KDP 표지용 PDF 파일

## Requirements

### Requirement 1: 프로젝트 초기화 및 설정 관리

**User Story:** As a 사용자, I want to YAML 설정 파일로 책 정보를 정의하고 싶습니다, so that 반복적인 입력 없이 여러 책을 효율적으로 생성할 수 있습니다.

#### Acceptance Criteria

1. WHEN 사용자가 설정 파일 경로를 지정하면, THE Pipeline SHALL 해당 YAML 파일을 파싱하여 Book_Config 객체로 변환한다
2. WHEN 설정 파일에 필수 필드(title, author, topic)가 누락되면, THE Pipeline SHALL 명확한 오류 메시지와 함께 실행을 중단한다
3. WHEN 설정 파일이 존재하지 않으면, THE Pipeline SHALL 파일 경로를 포함한 오류 메시지를 출력한다
4. THE Book_Config SHALL 다음 필드를 지원한다: id, title, author, topic, genre, language, cover.style, metadata, outline
5. WHEN outline 필드가 비어있으면, THE Content_Generator SHALL AI를 통해 목차를 자동 생성한다

### Requirement 2: 콘텐츠 생성

**User Story:** As a 사용자, I want to AI가 책 본문을 자동으로 생성하길 원합니다, so that 최소한의 노력으로 완성도 높은 콘텐츠를 얻을 수 있습니다.

#### Acceptance Criteria

1. WHEN 유효한 Book_Config가 제공되면, THE Content_Generator SHALL LLM API를 호출하여 마크다운 형식의 책 본문을 생성한다
2. THE Content_Generator SHALL 다음 LLM 백엔드를 지원한다: Ollama (로컬, 무료), Claude API (유료)
3. WHEN Ollama 백엔드가 선택되면, THE Content_Generator SHALL 로컬에서 실행 중인 Ollama 서버(http://localhost:11434)에 연결한다
4. WHEN Claude 백엔드가 선택되면, THE Content_Generator SHALL Anthropic API를 호출한다
5. WHEN outline이 제공되면, THE Content_Generator SHALL 해당 목차 구조를 따라 챕터별로 콘텐츠를 생성한다
6. THE Content_Generator SHALL 각 챕터를 1500-2000자 분량으로 생성한다
7. THE Content_Generator SHALL 생성된 마크다운을 로컬 파일 시스템에 저장한다
8. WHEN LLM API 호출이 실패하면, THE Content_Generator SHALL 재시도 로직을 수행하고 최종 실패 시 오류를 보고한다
9. THE Content_Generator SHALL 생성 진행 상황을 콘솔에 출력한다 (예: "Chapter 3/12 생성 중...")

### Requirement 3: 표지 디자인 생성

**User Story:** As a 사용자, I want to AI가 전문적인 책 표지를 자동으로 디자인하길 원합니다, so that 별도의 디자인 작업 없이 출판 가능한 표지를 얻을 수 있습니다.

#### Acceptance Criteria

1. WHEN 유효한 Book_Config가 제공되면, THE Cover_Designer SHALL Stable Diffusion API를 호출하여 표지 이미지를 생성한다
2. THE Cover_Designer SHALL 로컬 Stable Diffusion WebUI API 서버(http://localhost:7860)에 연결한다
3. THE Cover_Designer SHALL 장르(technology, business, fiction, self-help, science)에 따라 최적화된 프롬프트를 사용한다
4. THE Cover_Designer SHALL 생성된 이미지를 PNG 형식으로 로컬 파일 시스템에 저장한다
5. WHEN Stable Diffusion API 호출이 실패하면, THE Cover_Designer SHALL 오류 메시지를 출력하고 파이프라인을 중단한다
6. THE Cover_Designer SHALL 책 제목이 표지에 포함되도록 프롬프트를 구성한다

### Requirement 4: PDF 조립

**User Story:** As a 사용자, I want to 생성된 콘텐츠와 표지를 KDP 규격 PDF로 조립하길 원합니다, so that 바로 KDP에 업로드할 수 있는 파일을 얻을 수 있습니다.

#### Acceptance Criteria

1. WHEN 마크다운 콘텐츠와 표지 이미지가 준비되면, THE PDF_Assembler SHALL 본문 PDF(interior.pdf)와 표지 PDF(cover.pdf)를 생성한다
2. THE PDF_Assembler SHALL 한국어 폰트(Noto Sans KR)를 지원하여 한글 렌더링을 보장한다
3. THE Interior_PDF SHALL 타이틀 페이지, 헤더(책 제목), 푸터(페이지 번호)를 포함한다
4. THE Interior_PDF SHALL 마크다운 헤딩(##, ###)을 적절한 폰트 크기로 변환한다
5. THE Cover_PDF SHALL A4 크기(210x297mm)로 표지 이미지를 출력한다
6. WHEN 한국어 폰트 다운로드가 실패하면, THE PDF_Assembler SHALL 영문 폴백 폰트(Helvetica)를 사용한다

### Requirement 5: 파이프라인 실행 및 출력

**User Story:** As a 사용자, I want to CLI 명령어 하나로 전체 파이프라인을 실행하길 원합니다, so that 복잡한 단계 없이 책을 생성할 수 있습니다.

#### Acceptance Criteria

1. THE Pipeline SHALL `python run.py --config <path>` 형식의 CLI 인터페이스를 제공한다
2. WHEN 파이프라인이 완료되면, THE Pipeline SHALL 출력 디렉토리에 다음 파일들을 생성한다: manuscript.md, cover.png, interior.pdf, cover.pdf, manifest.json
3. THE Pipeline SHALL 각 단계(콘텐츠 생성, 표지 생성, PDF 조립)의 시작과 완료를 콘솔에 출력한다
4. THE manifest.json SHALL 책 메타데이터, 파일 경로, 생성 시간을 포함한다
5. WHEN 파이프라인 중 오류가 발생하면, THE Pipeline SHALL 어느 단계에서 실패했는지 명확히 표시한다
6. THE Pipeline SHALL 출력 디렉토리를 `output/<book_id>/` 형식으로 구성한다

### Requirement 6: API 키 및 백엔드 설정 관리

**User Story:** As a 사용자, I want to API 키와 백엔드 설정을 안전하게 관리하길 원합니다, so that 키가 코드에 노출되지 않고 유연하게 백엔드를 선택할 수 있습니다.

#### Acceptance Criteria

1. THE Pipeline SHALL 환경 변수에서 API 키를 읽는다 (ANTHROPIC_API_KEY for Claude)
2. WHEN 환경 변수가 설정되지 않으면, THE Pipeline SHALL `.env` 파일에서 API 키를 읽는다
3. THE Pipeline SHALL 설정 파일에서 LLM 백엔드를 선택할 수 있다 (llm_backend: ollama | claude)
4. WHEN Ollama 백엔드가 선택되면, THE Pipeline SHALL API 키 없이 로컬 서버에 연결한다
5. WHEN Claude 백엔드가 선택되고 API 키가 없으면, THE Pipeline SHALL 명확한 설정 안내 메시지와 함께 실행을 중단한다
6. THE Pipeline SHALL API 키를 로그나 출력에 노출하지 않는다

### Requirement 7: 오류 처리 및 복구

**User Story:** As a 사용자, I want to 파이프라인 실패 시 중간 결과물을 보존하길 원합니다, so that 처음부터 다시 시작하지 않아도 됩니다.

#### Acceptance Criteria

1. WHEN 콘텐츠 생성이 완료된 후 표지 생성에서 실패하면, THE Pipeline SHALL 생성된 마크다운 파일을 보존한다
2. THE Pipeline SHALL `--resume` 옵션을 제공하여 마지막 성공 단계부터 재개할 수 있다
3. WHEN 재개 모드로 실행하면, THE Pipeline SHALL 이미 존재하는 파일을 건너뛰고 다음 단계를 진행한다
4. THE Pipeline SHALL 각 단계 완료 시 상태를 `output/<book_id>/status.json`에 기록한다

### Requirement 8: 품질 검증 및 KDP 정책 준수

**User Story:** As a 사용자, I want to 생성된 콘텐츠가 KDP 정책을 준수하는지 자동으로 검증하길 원합니다, so that 계정 정지 위험 없이 안전하게 출판할 수 있습니다.

#### Acceptance Criteria

1. WHERE 품질 검증 옵션이 활성화되면, THE Pipeline SHALL 생성된 콘텐츠의 단어 수를 검증한다 (최소 10,000단어 권장)
2. WHERE 품질 검증 옵션이 활성화되면, THE Pipeline SHALL 최소 챕터 수(기본 5개)를 검증한다
3. THE Pipeline SHALL 중복 문장 비율을 검사하여 스팸 콘텐츠 위험을 경고한다
4. WHEN 품질 검증에 실패하면, THE Pipeline SHALL 경고 메시지를 출력하되 파이프라인은 계속 진행한다
5. THE Pipeline SHALL 품질 검증 결과를 manifest.json에 포함한다
6. THE manifest.json SHALL "ai_generated: true" 필드를 포함하여 KDP 업로드 시 AI 콘텐츠 표시를 상기시킨다

### Requirement 9: 비용 추적

**User Story:** As a 사용자, I want to API 사용 비용을 추적하길 원합니다, so that 예산을 관리하고 수익성을 계산할 수 있습니다.

#### Acceptance Criteria

1. THE Pipeline SHALL 각 API 호출의 토큰 사용량을 기록한다
2. THE Pipeline SHALL 예상 비용을 계산하여 manifest.json에 포함한다 (GPT-4o 토큰 비용 + DALL-E 이미지 비용)
3. WHEN 파이프라인이 완료되면, THE Pipeline SHALL 총 예상 비용을 콘솔에 출력한다
4. THE Pipeline SHALL 누적 비용을 `output/cost_summary.json`에 기록한다
