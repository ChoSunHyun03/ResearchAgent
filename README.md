# Company Research Agent

채용공고를 입력하면 기업과 직무 정보를 구조화하고,
관련 정보를 웹에서 검색해 출처를 포함한 Research Report를 제공하는 학습용 프로젝트입니다.

React 프론트엔드와 FastAPI 백엔드로 구성되어 있습니다.
채용공고 분석과 리서치 계획에는 OpenAI Structured Outputs를 사용할 수 있습니다.
개발용 mock 분석과 규칙 기반 계획을 유지하며, 보고서는 아직 snippet 기반입니다.

## 1. 프로젝트 목적

취업 준비 과정에서 반복하는 다음 작업을 하나의 흐름으로 연결합니다.

- 채용공고의 업무·필수조건·우대조건 정리
- 기업 주요 사업 조사
- 직무와 기술 관련 정보 조사
- 최근 뉴스와 기업 전략 검색
- 검색 결과와 출처 정리

기술 도입 자체보다 채용공고를 이해하고 지원 준비에 필요한 정보를 조사하는 데 목적이 있습니다.

현재는 사용자가 각 단계의 버튼을 눌러 진행합니다.
정보 충분 여부를 판단하거나 자동으로 재검색하는 Agent Loop는 아직 구현하지 않았습니다.

## 2. 현재 구현 상태

| 단계 | 구현 방식 |
|---|---|
| 채용공고 입력 | URL 입력 또는 직접 텍스트 입력 |
| URL 텍스트 추출 | 공개 주소 검증 + urllib3 + BeautifulSoup |
| Job Analysis | OpenAI Structured Outputs 또는 개발용 mock |
| Research Plan | OpenAI Structured Outputs 또는 규칙 기반 검색어 생성 |
| Web Research | DDGS 웹 검색 및 선택적 HTML 본문 수집 |
| Research Report | 검색 snippet과 출처를 주제별로 정리 |

### 완료한 개선

- STEP 1: OpenAI 환경설정과 클라이언트 생성 기반
- STEP 2: 실제 채용공고의 구조화 분석
- STEP 3: 설정으로 선택하는 LLM Research Planner
- STEP 4: 검색 결과 정제·주제별 상태 구분·평가용 예제 준비
- STEP 5: 제한된 페이지 본문 수집과 실패 시 snippet 유지

### 아직 구현하지 않은 기능

- 조사 이력과 결과의 데이터베이스 저장
- 출처 유형과 관련성 분류
- 여러 출처를 종합한 LLM Report
- 지원 준비 인사이트 생성
- 정보 충분 여부 평가와 추가 검색
- LangGraph Agent Loop
- MCP 검색·페이지 수집 도구
- Ollama Local LLM
- LoRA Fine-tuning
- GPU 및 vLLM Serving

## 3. Workflow

```text
채용공고 URL
→ 페이지 텍스트 추출
                         ┐
                         ├→ Job Analysis
직접 입력한 채용공고 텍스트 ┘
→ Research Plan
→ Web Research
→ 페이지 본문 수집 (선택)
→ Research Report
```

Job Analysis는 설정에 따라 두 가지 방식으로 동작합니다.

```text
analyze_job()
→ 입력 검증
→ 환경설정 확인
   ├─ USE_MOCK=true
   │  → mock JSON
   └─ USE_MOCK=false
      → OpenAI Structured Outputs
→ JobAnalysis
```

OpenAI 호출이 실패하면 오류를 반환합니다.
고정 mock 데이터를 실제 분석 결과로 오해하지 않도록 자동 fallback은 사용하지 않습니다.

## 4. Architecture

```text
React + TypeScript
        │
        │ HTTP 요청
        ▼
FastAPI — main.py
        │
        ▼
리서치 처리 — research.py
        ├─ 환경설정 — config.py
        ├─ 채용공고 분석 — llm/openai_provider.py
        ├─ 조사 계획 생성 — llm/research_planner.py
        ├─ 웹 검색 — search.py
        └─ URL 텍스트 추출 — scraper.py

입력·출력 모델 — models.py
분석 프롬프트 — prompts.py
```

HTTP 요청 처리, 리서치 로직, 외부 API 호출, 데이터 모델을 분리합니다.
현재 LLM Provider는 OpenAI만 지원합니다.

## 5. 주요 기능

### 5.1 채용공고 입력

- 채용공고 URL 입력
- 채용공고 텍스트 직접 입력
- URL에서 추출한 텍스트를 화면에서 확인하고 편집 가능

URL 수집은 공개 주소 검증 후 urllib3와 BeautifulSoup을 사용합니다.
본문 영역을 우선하며 공고 입력에는 최대 20,000자를 반환합니다.
JavaScript 렌더링이나 로그인이 필요한 페이지는 수집이 제한될 수 있습니다.

### 5.2 Job Analysis

기존 `JobAnalysis` Pydantic 모델을 OpenAI Structured Outputs에 연결합니다.

```text
company: str
position: str
responsibilities: list[str]
requirements: list[str]
preferred: list[str]
keywords: list[str]
```

분석 규칙은 다음과 같습니다.

- 제공된 공고에 명시된 정보를 추출
- 업무·필수조건·우대조건을 구분
- 없는 회사명·직무명은 빈 문자열로 처리
- 없는 목록 정보는 빈 배열로 처리
- 외부 지식으로 정보를 보충하지 않도록 지시
- 공고 내부 명령문은 분석 대상 데이터로 취급

이 규칙은 프롬프트에 정의되어 있습니다.
Structured Outputs가 출력 형식을 맞추더라도 내용 정확성까지 보장하지는 않으므로 원문 대조가 필요합니다. 지원 직무 선택 역시 내용 검증을 대체하지 않습니다.

입력은 앞뒤 공백을 제거한 뒤 검증합니다.

- 빈 문자열·공백만 있는 입력 거부
- 20,000자 초과 입력 거부

### 지원 직무 선택과 전체 채용공고

분석 요청에 선택적 `target_position`을 전달합니다. 단일 직무 공고는 자동으로 핵심 정보를 표시하고,
여러 직무가 있으면 후보 버튼에서 지원 직무를 먼저 선택합니다.
직무 직접 입력은 **지원 직무를 직접 지정하고 싶어요 / 다른 직무로 확인하기**에서 사용할 수 있습니다.

화면은 **공고 입력 → 직무 확인 → 핵심 정보·기업 조사** 순서로 진행합니다.
URL의 **공고 확인하기**는 공고와 직무 목록을 수집합니다.
SK브로드밴드 Junior Talent 사이트는 연결된 공개 직무 데이터를 읽어 **직군 → 세부 직무** 버튼을 생성합니다.
버튼 개수와 조건은 수집 데이터에 따라 바뀌며, 목록 수집에는 LLM을 호출하지 않습니다.
선택하면 **그 직무의 상세 본문 + 공통 지원자격**만 분석합니다. 같은 공고에서 분석을 완료한 직무는 현재 화면에서 재사용합니다.
다른 사이트는 기존 HTML·LLM 분석 경로를 유지합니다. 직접 붙여넣기도 지원합니다.
가져온 원문은 기본적으로 접혀 있으며 필요할 때 확인·수정할 수 있습니다.
분석이 준비되면 회사·직무와 주요 업무·지원자격·필수/필요 역량·우대사항·키워드를 표시합니다.
선택이나 상세 공고가 필요한 동안에는 빈 분석표와 기업 조사 영역을 표시하지 않습니다.

조사 항목을 만들고 → 자료 검색 → 보고서 만들기를 순서대로 진행합니다.
검색어·조사 이유·검색 자료·수집한 원문은 펼쳐보기로 확인합니다.
화면에는 내부 오류 코드·수집 시각·리다이렉트 주소 대신 사용자에게 필요한 상태를 안내합니다.
본문 수집은 선택 기능이며 현재 보고서가 검색 요약을 사용하는 동작은 유지합니다.
입력 방식·URL·원문이 바뀌면 이전 결과를 초기화하고, 직무를 재분석할 때 조사 결과도 초기화합니다.

| analysis_status | 동작 |
|---|---|
| ready | 단일 직무 또는 지정 직무 분석 완료, 계획 생성 가능 |
| needs_selection | 여러 모집 직무 중 선택 필요, 후보 버튼으로 재분석 |
| missing_details | 직무별 본문 부족, 상세 공고 입력 필요 |

분석 결과에는 기존 여섯 필드와 함께 `available_positions`, `analysis_message`가 있습니다.
대기 상태에서는 업무·조건·키워드와 직무명을 비워 다른 직무의 정보가 후속 단계에 섞이지 않게 합니다.
선택한 직무의 조건과 명시적 공통 지원자격만 추출하도록 지시하고,
반환 직무와 사용자 선택이 다르면 서버가 진행을 차단합니다.
직무명은 공고의 표기와 맞춰 입력하거나 후보 버튼을 사용합니다. 임의의 별칭 자동 매칭은 지원하지 않습니다.
`Junior Talent`나 `신입사원` 등 채용 유형은 직무로 사용하지 않습니다.
후보 발견과 조건 분리는 LLM 판단이며 추출 정확성이 보장되는 것은 아닙니다.

URL 수집은 main 전체 또는 여러 article을 읽고 채용 제목을 포함합니다.
200자 미만의 수집 결과에는 확인 안내를 표시하며, 이 기준은 참고용입니다.
이미지·별도 API·동적 화면에만 있는 직무 내용은 자동으로 가져오지 못할 수 있습니다.
그 경우 원하는 직무의 상세 페이지 URL이나 텍스트를 제공해야 합니다.

DB 없이도 지원 직무를 명시하거나 후보에서 선택할 수 있습니다.
STEP 8에서는 사용자가 확인한 선호 직무와 실행별 선택 직무를 저장할 예정입니다.
과거 지원 이력은 선택 제안의 근거이며 현재 공고의 지원 직무를 자동 확정하지 않습니다.

### 5.3 Research Plan

USE_LLM_PLANNER=true에서는 JobAnalysis의 여섯 필드를 활용해
직무에 맞는 조사 항목 5~7개를 생성합니다.

USE_LLM_PLANNER=false에서는 기존 규칙 기반 계획을 사용합니다.

각 항목은 topic, query, reason으로 구성됩니다.
빈 항목과 동일 검색어 중복을 검증하며,
회사명과 직무명은 원본 분석 결과를 유지합니다.

계획은 조사 질문이며, 회사에 대한 확인된 사실이 아닙니다.
검색과 Report 생성은 기존 방식을 유지합니다.

회사명 또는 직무명이 비어 있으면 계획 생성을 거부합니다.
LLM 오류 발생 시 규칙 기반으로 자동 전환하지 않고 오류를 반환합니다.

### 5.4 Web Research

DDGS로 검색어별 최대 여섯 개의 후보를 요청하고, 정제 후 최대 세 개를 반환합니다.

- 제목과 snippet의 공백 정리
- HTTP(S) URL 검증, 일반 추적 파라미터와 fragment 제거
- 같은 주제 안에서 같은 URL의 중복 제거, 먼저 나온 순위 유지
- 의미 있는 URL 파라미터·인코딩·경로 보존
- URL이 없거나 제목과 snippet이 모두 비어 있는 항목 제외
- 다른 주제에서 사용되는 동일 출처는 각 주제에 유지

각 검색 주제에는 기존 `results`와 함께 다음 상태를 반환합니다.

| status | 의미 |
|---|---|
| success | 표시할 수 있는 정제 결과가 있음 |
| no_results | 검색 호출은 완료되었으나 정제 후 결과가 없음 |
| error | 검색 호출 실패 또는 잘못된 검색어·응답 |

오류에는 `error_kind`와 안전한 `error_message`가 포함됩니다.
시간 초과·요청 제한·검색 서비스 오류·잘못된 응답·잘못된 검색어를 구분합니다.
한 주제가 실패해도 다른 주제의 검색과 보고서 생성은 계속합니다.
부분 실패를 포함한 정상 요청은 HTTP 200이고, 상태는 주제별로 확인합니다.
DDGS가 예외를 반환한 경우 실제로 정보가 없는지 단정하지 않고 오류로 표시합니다.

검색 결과 정제는 관련성 판정이나 출처 사실 검증이 아닙니다.
검색 결과 화면의 **페이지 본문 수집** 버튼은 `POST /api/research/collect`를 호출합니다.
검색 결과의 기존 제목·URL·snippet을 유지하며 선택적 `page` 객체를 추가합니다.

| page 필드 | 의미 |
|---|---|
| status | success / error / skipped |
| text, title | 추출한 본문과 HTML 제목 |
| final_url | 리다이렉트 후 최종 URL |
| fetched_at | 성공한 수집 시각 (UTC) |
| truncated | 본문 길이 제한 적용 여부 |
| error_kind, error_message | 실패·생략 이유 |

`page=null`이면 아직 본문을 수집하지 않은 결과입니다.
주제별 검색 상태와 페이지별 수집 상태는 서로 독립적입니다.
검색에 성공해도 해당 페이지 접근은 실패할 수 있습니다.

수집 제한은 요청당 고유 URL 최대 10개, 리다이렉트 최대 3회,
페이지별 전송·압축 해제 HTML 각각 1,000,000바이트, 본문 최대 12,000자입니다.
같은 요청의 URL 중복은 수집 결과를 재사용합니다. 실패한 페이지의 snippet은 유지합니다.
페이지별 8초·전체 45초의 진행 예산과 연결·읽기 timeout을 적용하지만,
운영체제 DNS 조회와 블로킹 읽기 때문에 전체 요청 시간이 정확히 그 안에 끝나는 것은 아닙니다.

HTTP(S)의 80·443 포트, 공개 IP만 허용하고 리다이렉트마다 다시 검증합니다.
검증한 IP로 직접 연결하며 HTTPS 인증서와 SNI는 원래 호스트 이름을 사용합니다.
HTML과 gzip을 지원하고 PDF·로그인·JavaScript 렌더링·기타 압축 형식은 지원하지 않습니다.
사이트에 따라 본문 추출이 불완전할 수 있습니다. 환경변수 HTTP 프록시는 사용하지 않습니다.

현재 보고서는 계속 검색 snippet을 사용합니다.
수집 본문은 화면에서 확인할 수 있고 STEP 7의 LLM Report 입력으로 활용할 예정입니다.

### 5.5 Research Report

검색 결과를 주제별로 묶고 다음 내용을 제공합니다.

- 조사 주제
- 검색어
- 검색 snippet 목록
- 출처 제목과 URL

현재는 snippet을 정리하는 방식입니다. 검색 상태와 오류도 보고서에 전달하여
검색 실패를 단순한 정보 부족과 구분합니다.
여러 출처의 사실을 종합하거나 지원 준비 인사이트를 생성하는 LLM 요약은 아직 없습니다.

## 6. Tech Stack

| 영역 | 기술 |
|---|---|
| Frontend | React, TypeScript, Vite |
| Backend | Python, FastAPI |
| 데이터 검증 | Pydantic |
| 채용공고 분석 | OpenAI Python SDK, Structured Outputs |
| 환경설정 | python-dotenv, dataclass |
| 검색 | DDGS |
| 페이지 수집 | urllib3, BeautifulSoup |
| 자동 테스트 | unittest, unittest.mock |

백엔드 직접 의존성 버전은 `requirements.txt`에 기록합니다.
프론트엔드 의존성은 `package.json`과 `package-lock.json`으로 관리합니다.

## 7. Project Structure

```text
ResearchAgent/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── config.py
│   │   ├── research.py
│   │   ├── search.py
│   │   ├── scraper.py
│   │   ├── prompts.py
│   │   └── llm/
│   │       ├── __init__.py
│   │       ├── openai_provider.py
│   │       └── research_planner.py
│   └── tests/
│       ├── test_config.py
│       ├── test_job_analysis.py
│       ├── test_job_selection.py
│       ├── test_research_plan.py
│       ├── test_search.py
│       ├── test_web_research.py
│       ├── test_scraper.py
│       ├── test_source_collection.py
│       └── fixtures/
│           ├── search_cases.json
│           └── source_page.html
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── App.css
│   │   ├── api.ts
│   │   ├── main.tsx
│   │   └── index.css
│   ├── public/
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.ts
├── docs/
│   └── planning.md
├── evaluation/
│   ├── README.md
│   └── job_analysis_cases.json
├── mock_data/                 # 로컬 개발용, Git 제외
│   └── interx.json
├── mock_data.example.json
├── requirements.txt
├── .env                      # 로컬 설정, Git 제외
├── .env.example
├── .gitignore
└── README.md
```

### 주요 파일 역할

| 파일 | 역할 |
|---|---|
| main.py | API 라우트와 HTTP 오류 처리 |
| models.py | 입력·분석·계획·검색·보고서 모델 |
| config.py | 루트 .env 로딩과 설정 검증 |
| research.py | 분석 분기와 리서치 처리 |
| openai_provider.py | SDK 클라이언트 생성과 구조화 분석 |
| research_planner.py | LLM 조사 계획 생성과 결과 검증 |
| prompts.py | 분석·계획 생성 프롬프트 |
| search.py | DDGS 검색 |
| scraper.py | 공개 주소 검증·제한된 HTML 수집·본문 추출 |
| App.tsx | 입력·결과 화면과 단계별 실행 |
| api.ts | 프론트엔드의 API 요청 |
| planning.md | 개발 과정과 검증 기록 |

## 8. 실행 환경 준비

개발 환경은 Python 3.12를 사용합니다.
프론트엔드 실행에는 Vite가 지원하는 Node.js와 npm이 필요합니다.

아래 명령은 프로젝트 루트에서 실행합니다.

### 8.1 백엔드 의존성

가상환경이 없다면 먼저 생성합니다.

```bash
python3 -m venv .venv
```

가상환경을 활성화하고 설치합니다.

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
```

### 8.2 환경변수

처음 내려받은 환경에서 `.env`가 없다면 예제 파일을 복사합니다.

```bash
cp .env.example .env
```

이미 `.env`가 있다면 덮어쓰지 말고 기존 파일을 편집합니다.

OpenAI 모드 설정 예시:

```dotenv
USE_MOCK=false
USE_LLM_PLANNER=true
LLM_PROVIDER=openai
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
```

실제 API Key는 로컬 `.env`의 `OPENAI_API_KEY=` 뒤에 입력합니다.
모델은 계정에서 사용할 수 있고 Structured Outputs를 지원하는 모델로 설정합니다.

- `.env`와 `.env.*`는 Git에서 제외
- 값이 없는 `.env.example`은 Git에 포함
- 기존 시스템 환경변수가 `.env`보다 우선
- Key 없이 전체 개발 흐름을 사용하려면 `USE_MOCK=true`, `USE_LLM_PLANNER=false` 설정
- `USE_MOCK`는 공고 분석만 제어하며, LLM 계획은 `USE_LLM_PLANNER`로 별도 선택
- 실제 OpenAI 호출에는 API 사용 비용 발생

`.env`를 변경한 뒤에는 서버를 완전히 종료하고 다시 실행합니다.

### 8.3 Mock 모드

실제 API 없이 개발할 때는 다음을 설정합니다.

```dotenv
USE_MOCK=true
USE_LLM_PLANNER=false
LLM_PROVIDER=openai
OPENAI_API_KEY=
OPENAI_MODEL=
```

현재 mock 모드는 `mock_data/interx.json`을 읽습니다.
이 파일은 Git에 포함되지 않습니다.

새로 내려받은 환경에서는 공개 예제로 테스트용 파일을 준비할 수 있습니다.

```bash
mkdir -p mock_data
cp mock_data.example.json mock_data/interx.json
```

위 복사 명령은 기존 mock 파일이 없는 환경에서 사용합니다.
예제를 사용하면 입력 내용과 관계없이 예제 회사·직무가 반환됩니다.

### 8.4 프론트엔드 의존성

```bash
cd frontend
npm ci
```

## 9. 서버 실행

### 9.1 Backend

프로젝트 루트에서 실행합니다.

```bash
source .venv/bin/activate
python -m uvicorn backend.app.main:app --reload
```

- 서버: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

### 9.2 Frontend

별도 터미널에서 실행합니다.

```bash
cd frontend
npm run dev
```

Vite가 출력한 주소로 접속합니다.

현재 프론트엔드 API 주소는 `http://localhost:8000`입니다.
백엔드 CORS는 `http://localhost:5173`과 `http://localhost:5174`를 허용합니다.

다른 포트를 사용하려면 API 주소와 CORS 설정도 확인해야 합니다.

## 10. API Endpoints

| Method | Endpoint | 역할 |
|---|---|---|
| GET | /health | 서버 상태 확인 |
| POST | /api/jobs/fetch | URL에서 텍스트 추출 |
| POST | /api/jobs/analyze | 채용공고 분석 |
| POST | /api/research/plan | 리서치 계획 생성 |
| POST | /api/research/search | 웹 검색 실행 |
| POST | /api/research/collect | 검색 결과의 페이지 본문 수집 |
| POST | /api/research/report | 보고서 생성 |

### 분석 요청 예시

아래 입력은 테스트용 가상 공고입니다.

```bash
curl -sS -i -X POST http://localhost:8000/api/jobs/analyze \
  -H 'Content-Type: application/json' \
  -d '{"job_text":"테스트회사 AI Engineer 채용. 주요 업무: 모델 API 개발. 필수조건: Python 경험. 우대조건: Docker 경험."}'
```

반환 형식 예시:

```json
{
  "company": "테스트회사",
  "position": "AI Engineer",
  "responsibilities": ["모델 API 개발"],
  "requirements": ["Python 경험"],
  "preferred": ["Docker 경험"],
  "keywords": ["AI Engineer", "Python", "Docker"]
}
```

목록 표현과 키워드는 모델 응답에 따라 달라질 수 있습니다.

## 11. 테스트와 검증

### 11.1 자동 테스트

프로젝트 루트에서 실행합니다.

```bash
source .venv/bin/activate
python -m unittest discover -s backend/tests -p "test_*.py" -v
```

현재 자동 테스트는 총 77개입니다.

| 파일 | 개수 | 주요 검증 |
|---|---:|---|
| test_config.py | 8 | 환경 로딩, 기본값, 우선순위, 설정 검증, 클라이언트 생성 |
| test_job_analysis.py | 10 | 입력 검증, 분석 분기, 출력 형식, 거절·미완성 응답, API 오류 변환 |
| test_job_selection.py | 10 | 초기 사용자 직무 선택, 대상 전달, 혼합 방지, 상세 부족, 계획 차단, 채용 유형 제외 |
| test_research_plan.py | 9 | 계획 생성 분기, 원본 정보 유지, 개수·공백·중복 검증, 구조화 출력, 오류 변환 |
| test_search.py | 7 | 검색 정제 예제, URL 보존, 검색 인자, 빈 결과, 외부 오류 구분 |
| test_web_research.py | 6 | 부분 실패, 출처 재사용, 기존 요청 호환, ASGI 검색→보고서 연결, 평가 예제 구조 |
| test_scraper.py | 20 | URL·IP·리다이렉트 검증, TLS 호스트, timeout·크기·gzip·추출·공고 호환 |
| test_source_collection.py | 7 | URL 재사용, 부분 실패, 예산, 수집→보고서 API, 기존 공고 endpoint 호환 |

자동 테스트는 외부 OpenAI·DDGS·페이지 HTTP 호출을 대체합니다.
실제 API Key의 유효성, 모델 접근 권한, 추출 정확성을 확인하는 테스트는 아닙니다.

### 11.2 수동 검증

다음 입력과 흐름을 확인합니다.

- 정상 채용공고
- 필수조건이 없는 공고
- 우대조건이 없는 공고
- 매우 짧은 공고
- 빈 입력
- 실제 공고와 추출 결과 대조
- mock 모드 회귀
- 분석 → 계획 → 검색 → 보고서 연결

개발 중 자동 테스트와 API 동작 확인을 진행했습니다.
평가 데이터셋을 활용한 정확도·응답시간·비용의 정량 평가는 아직 수행하지 않았습니다.

세부 검증 결과는 `docs/planning.md`에 기록합니다.
가상 공고 네 개의 기대 분석과 계획 검토 기준은 `evaluation/`에 있습니다.
정제 예제 네 개는 자동 테스트에 사용하며, 모델 품질의 정량 평가 실행기는 아직 없습니다.

## 12. 분석 API 오류 처리

| 상황 | HTTP 상태 |
|---|---:|
| 빈 입력·입력 길이 초과 | 422 |
| 모델의 분석 거절 | 422 |
| 환경설정 누락·오류 | 503 |
| 인증·권한·연결·사용 한도 문제 | 503 |
| OpenAI 요청 실패 | 502 |
| 구조화 출력 오류·불완전 응답 | 502 |
| 요청 timeout | 504 |
| mock 파일 읽기·구조 오류 | 500 |

현재 프론트엔드는 일부 오류를 일반적인 메시지로 표시합니다.
상세 원인은 Swagger 또는 API 응답의 `detail`에서 확인할 수 있습니다.

## 13. 현재 한계

- 생성된 계획의 검색 적합성은 아직 정량 평가하지 않음
- 조사 이력과 보고서는 DB에 저장하지 않음
- JavaScript 렌더링·로그인이 필요한 채용사이트 수집 제한
- HTML 구조에 따라 본문 일부만 추출되거나 공통 영역이 섞일 수 있음
- 모집 직무 후보와 해당 조건의 분리는 LLM 판단에 의존하며 원문 대조 필요
- 본문 수집은 고유 URL 10개와 크기·시간 예산 안에서만 수행
- URL 중복 제거는 주제별로 수행하며 의미가 비슷한 내용의 중복은 판정하지 않음
- 관련성 필터·출처 신뢰도 분류 미구현
- Report는 검색 snippet 목록을 정리하는 수준
- 주장별 출처 연결과 상충 정보 분석 미구현
- 개인 지원자 이력과 연결한 인사이트 미구현
- 자율 재검색과 Agent Loop 미구현
- PDF·기타 압축 형식·환경변수 HTTP 프록시 미지원
- OS DNS 조회에 대한 강제 종료와 엄격한 전체 요청 시간 제한 미구현
- 출력 형식이 정상이어도 LLM 추출 내용에 오류가 있을 수 있음

## 14. 향후 개선 방향

각 단계는 기존 기능을 유지하면서 구현하고 검증합니다.

| STEP | 작업 |
|---|---|
| 1 | OpenAI 환경 구성 |
| 2 | OpenAI Job Analysis |
| 3 | LLM Research Planner |
| 4 | 검색 결과 정제와 평가용 예제 준비 |
| 5 | 검색된 페이지 본문 수집 |
| 6 | 출처 유형과 관련성 분류 |
| 7 | 출처 기반 LLM Research Report |
| 8 | SQLite로 조사 이력·결과 저장 및 조회 |
| 9 | 직무 기반 지원 준비 인사이트 |
| 10 | 정보 충분 여부 평가와 제한된 추가 검색 |
| 11 | LangGraph 기반 상태·분기·반복 관리 |
| 12 | 기존 리서치 기능을 제공하는 MCP 서버 |
| 13 | 모델 Provider 정리와 Ollama 연결 |
| 14 | 모델 품질·속도·비용 평가 |
| 15 (선택) | GPU 추론 서빙 실험 |
| 16 (선택) | LoRA 파인튜닝 실험 |
| 17 (선택) | 학습 모델 서빙과 최종 문서 정리 |

STEP 8에서는 실행 ID·상태·시각·실패 원인, 분석·계획·검색 출처·보고서를 저장하고
이력 목록과 상세 조회 API 및 화면을 추가합니다. 확인한 선호 직무와 실행별 선택 직무도 저장합니다.
현재 선택이 우선이며 이력만으로 지원 직무를 확정하지 않습니다. 로그인과 Vector DB는 포함하지 않습니다.
평가용 예제는 STEP 4부터 준비하고, STEP 14에서 모델 간 비교를 수행합니다.
선택 단계는 장비·예산과 평가 결과를 확인한 후 진행합니다.

MCP는 검색과 페이지 수집 같은 외부 자원 접근 도구를
Agent 구현에서 분리하기 위해 검토합니다.

LoRA는 최신 회사 정보를 학습시키기보다
공고 구조화와 출력 형식 등 반복적인 작업 패턴 개선을 대상으로 검토합니다.

아직 구현하지 않은 기술을 현재 기능으로 소개하지 않습니다.

## 15. 개발 원칙

- 기존 endpoint와 데이터 모델을 가능한 한 유지
- 단계별 구현과 테스트
- API Key와 토큰을 코드·로그·Git에 포함하지 않음
- 외부 입력과 API 오류 구분
- 필요한 라이브러리만 추가
- 구현 범위와 한계를 문서에 기록
- 실제로 확인한 결과만 평가 내용으로 작성

작업은 기존 `openai-enviroment` 브랜치에서 진행합니다.
한 번에 하나의 STEP만 구현·검증·문서화하고 GitHub에 반영합니다.
변경 설명은 구현 이유, 코드 흐름, 검증 결과를 중심으로 제공합니다.


### 직무 자동 수집과 사용량 확인 (2026-10-15)

- SK브로드밴드 공고는 정적 HTML에 없는 직무를 `script[src]`의 공개 JD 데이터 파일에서 추가 수집합니다.
- 새 `job_postings.py`는 직군과 세부 직무 목록을 읽고 업무·자격요건·필요 역량·우대사항을 각각 보관합니다.
- JS 실행 또는 eval 없이 문자열·배열·객체·불리언만 해석하며, 함수 코드는 읽지 않습니다.
- 기존 공개 URL 검사·검증 IP 고정·리다이렉트 재검증·TLS·8초/1MB 제한을 재사용합니다. HTML과 JS는 각각 제한됩니다.
- `/api/jobs/fetch`의 `job_text`, `warnings`는 유지하며 `company`, `roles`, `source_url`을 추가합니다.
- `roles[].analysis_text`는 선택 직무와 공통 지원자격으로만 구성됩니다. 타 직무 조건은 포함하지 않습니다.
- 기존 `JobAnalysis` 필드를 유지하고 기본 빈 목록의 `competencies`를 추가합니다. 대기 상태에서는 역량도 초기화합니다.
- 사이트별 어댑터는 현재 SK브로드밴드 Junior Talent만 지원합니다. 다른 동적 사이트의 자동 수집과 브라우저 기반 보완은 후속 작업입니다.
- 사이트 구조나 데이터 형식이 변경되면 원문·경고를 유지하고 기존 분석/직접 입력으로 진행할 수 있습니다.

**API 사용량·비용**

OpenAI 응답의 실제 `usage`를 `llm_usage` 서버 로그와 `X-LLM-Usage` 응답 헤더로 전달합니다.
사용자 요청에 따라 프론트엔드의 토큰·비용 표시는 제거했습니다. 호출별 입력·캐시 입력·출력 토큰과 USD 계산값은 서버 로그에서 확인합니다.
현재 요금표는 2026-10-15 확인 기준 `gpt-4.1-mini`와 해당 스냅샷의 표준 입력 $0.40 / 캐시 입력 $0.10 / 출력 $1.60 (100만 토큰당)입니다.
[공식 요금](https://developers.openai.com/api/docs/models/gpt-4.1-mini), [토큰 사용량](https://developers.openai.com/api/docs/guides/token-counting)

`((입력 - 캐시 입력) × 입력 단가 + 캐시 입력 × 캐시 단가 + 출력 × 출력 단가) / 1,000,000`

이 값은 보고된 응답 토큰 기준 예상 비용이며 세금·환율·별도 재시도·usage를 받지 못한 실패 요청을 포함한 최종 청구액은 아닙니다.
요금표에 없는 모델은 토큰만 표시하고 비용은 미등록으로 안내합니다. 단가 변경 시 요금표를 갱신해야 합니다.
직무 분석 캐시는 현재 화면에서만 유지하며 새로고침 시 초기화됩니다. 사용량 로그의 DB 저장은 STEP 8에서 진행합니다.
서버 로그에는 공고 원문·API 키를 기록하지 않습니다. 호출 사용량 로그는 실행 중인 서버 터미널에서 확인합니다.

검증: 백엔드 92개, 프론트엔드 build·lint, 실제 직군 4개/세부 직무 6개와 AT/DT 분석·재선택 캐시·사용량 표시,
390px 화면에서 가로 넘침 없음 확인. 채용 일정의 구조화와 개인 지원 일정 저장은 이번 작업에 포함하지 않습니다.
