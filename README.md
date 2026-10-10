# Company Research Agent

채용공고를 입력하면 기업과 직무 정보를 구조화하고,
관련 정보를 웹에서 검색해 출처를 포함한 Research Report를 제공하는 학습용 프로젝트입니다.

React 프론트엔드와 FastAPI 백엔드로 구성되어 있습니다.
현재 채용공고 분석에는 OpenAI Structured Outputs를 사용하고,
리서치 계획과 보고서는 기존 규칙 기반 방식을 유지합니다.

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
| URL 텍스트 추출 | requests + BeautifulSoup |
| Job Analysis | OpenAI Structured Outputs 또는 개발용 mock |
| Research Plan | 규칙 기반 검색어 생성 |
| Web Research | DDGS 웹 검색 |
| Research Report | 검색 snippet과 출처를 주제별로 정리 |

### 완료한 개선

- STEP 1: OpenAI 환경설정과 클라이언트 생성 기반
- STEP 2: 실제 채용공고의 구조화 분석

### 아직 구현하지 않은 기능

- LLM 기반 Research Planning
- 검색 결과 중복 제거와 출처 분류
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

URL 수집은 requests와 BeautifulSoup을 사용합니다.
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
Structured Outputs가 출력 형식을 맞추더라도 내용 정확성까지 보장하지는 않으므로 원문 대조가 필요합니다.

입력은 앞뒤 공백을 제거한 뒤 검증합니다.

- 빈 문자열·공백만 있는 입력 거부
- 20,000자 초과 입력 거부

### 5.3 Research Plan

회사명, 직무명, 키워드 앞의 세 개를 사용해
다음 다섯 주제의 검색어를 생성합니다.

- 기업 주요 사업
- 지원 직무
- 핵심 기술
- 최근 뉴스
- 기업 전략

각 항목에는 `topic`, `query`, `reason`이 포함됩니다.
현재는 고정 주제와 템플릿을 사용하는 규칙 기반 방식입니다.

### 5.4 Web Research

DDGS로 검색어별 최대 세 개의 결과를 수집합니다.

검색 결과는 다음 필드로 구성됩니다.

- title
- url
- snippet

검색어는 순차적으로 실행합니다.
DDGS 예외는 빈 결과로 처리하여 후속 흐름을 유지합니다.

### 5.5 Research Report

검색 결과를 주제별로 묶고 다음 내용을 제공합니다.

- 조사 주제
- 검색어
- 검색 snippet 목록
- 출처 제목과 URL

현재는 snippet을 정리하는 방식입니다.
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
| 페이지 수집 | requests, BeautifulSoup |
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
│   │       └── openai_provider.py
│   └── tests/
│       ├── test_config.py
│       └── test_job_analysis.py
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
| prompts.py | 분석 프롬프트 |
| search.py | DDGS 검색 |
| scraper.py | URL에서 텍스트 추출 |
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
LLM_PROVIDER=openai
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
```

실제 API Key는 로컬 `.env`의 `OPENAI_API_KEY=` 뒤에 입력합니다.
모델은 계정에서 사용할 수 있고 Structured Outputs를 지원하는 모델로 설정합니다.

- `.env`와 `.env.*`는 Git에서 제외
- 값이 없는 `.env.example`은 Git에 포함
- 기존 시스템 환경변수가 `.env`보다 우선
- Key가 없는 상태에서도 mock 모드는 사용 가능
- 실제 OpenAI 호출에는 API 사용 비용 발생

`.env`를 변경한 뒤에는 서버를 완전히 종료하고 다시 실행합니다.

### 8.3 Mock 모드

실제 API 없이 개발할 때는 다음을 설정합니다.

```dotenv
USE_MOCK=true
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

현재 자동 테스트는 총 18개입니다.

| 파일 | 개수 | 주요 검증 |
|---|---:|---|
| test_config.py | 8 | 환경 로딩, 기본값, 우선순위, 설정 검증, 클라이언트 생성 |
| test_job_analysis.py | 10 | 입력 검증, 분석 분기, 출력 형식, 거절·미완성 응답, API 오류 변환 |

자동 테스트는 외부 OpenAI 호출을 대체합니다.
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

- Research Plan은 고정된 다섯 주제의 규칙 기반 방식
- 업무·필수조건·우대조건을 활용한 동적 계획 미구현
- JavaScript 렌더링·로그인이 필요한 채용사이트 수집 제한
- URL 수집 시 페이지 전체 텍스트의 앞 20,000자만 사용
- 검색 결과 중복 제거·관련성 필터·출처 신뢰도 분류 미구현
- DDGS 실패와 검색 결과 없음을 동일한 빈 결과로 처리
- Report는 검색 snippet 목록을 정리하는 수준
- 주장별 출처 연결과 상충 정보 분석 미구현
- 개인 지원자 이력과 연결한 인사이트 미구현
- 자율 재검색과 Agent Loop 미구현
- URL 수집의 내부 주소·리다이렉트 접근 제한 미구현
- 출력 형식이 정상이어도 LLM 추출 내용에 오류가 있을 수 있음

## 14. 향후 개선 방향

각 단계는 기존 기능을 유지하면서 구현하고 검증합니다.

1. LLM 기반 Research Planner
2. Python 기반 검색 결과 정제
3. 출처 유형과 신뢰도 분류
4. 출처를 추적할 수 있는 LLM Report
5. 직무 기반 지원 준비 인사이트
6. 정보 충분 여부 평가와 제한된 추가 검색
7. LangGraph 기반 조건 분기와 반복 제어
8. 검색·페이지 수집 기능의 MCP Tool 분리
9. 평가 데이터셋 구축과 Ollama 비교
10. 필요성이 확인된 경우 LoRA·GPU·vLLM 실험

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

현재 STEP 1과 STEP 2 작업은 `openai-enviroment` 브랜치에서 진행합니다.