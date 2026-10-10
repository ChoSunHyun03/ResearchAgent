# Company Research Agent

채용공고를 기반으로 기업과 직무에 필요한 정보를 자동으로 조사하고,
출처 기반 Research Report를 생성하는
기업 리서치 Agent MVP입니다.

## Project Goal

취업 준비 과정에서 반복적으로 수행하는 

- 기업 사업 분석
- 직무 조사
- 기술 키워드 조사
- 최근 뉴스 확인
- 기업 전략 조사

과정을 하나의 Workflow로 자동화하는 것을 목표로 했습니다. 

## Workflow

Job Posting URL / TEXT
→ Job Analysis
→ Research Plan
→ Web Research
→ Research Report

## Main Features

### 1. Job Posting Input

- 채용공고 URL 입력
- 직접 테스트 입력
- requests + BeautifulSoup 기반 텍스트 추출

### 2. Job Analysis

채용공고를 다음 구조로 분석합니다.

- Company
- Position
- Responsibilities
- Requirements
- Preferred Qualifications
- keywords

현재 MVP에서는 Mock Data 기반으로 동작하며,
추후 LLM API 연동이 가능하도록 구조를 분리했습니다.

### 3. Research Planner

채용공고 분석 결과를 기반으로
다음 Research Query를 생성합니다.

- 기업 주요 사업
- 지원 직무
- 핵심 기술
- 최근 뉴스 
- 기업 전략

### 4. Web Research

DDGS를 활용하여 
각 Research Query에 대해 실제 웹 검색을 수행합니다.

검색 결과는 다음 정보를 포함합니다.
- title
- url
- snippet

### 5. Research Report

Web Research 결과를 Topic별로 정리하고
출처와 함께 Research Report 형태로 제공합니다.

## Tech Stack

### Frontend
- React
- TypeScript
- Vite

### Backend
- Python
- FastAPI
- Pydantic

## Research
- DDGS
- requests
- BeautifulSoup

## Project Structure

```text
ResearchAgent/
├── backend/
│   └── app/
│       ├── main.py
│       ├── models.py
│       ├── research.py
│       ├── search.py
│       ├── scraper.py
│       └── prompts.py
│
├── frontend/
│   └── src/
│       ├── App.tsx
│       ├── App.css
│       └── api.ts
│
├── docs/
│   └── planning.md
│
└── README.md
```
---
### Current Limitations
- Job Analysis는 현재 Mock Data 기반
- JavaScript 기반 동적 채용공고 페이지 수집 제한
- 검색 결과 snippet 기반
- 여러 출처를 종합한 자연어 요약은 아직 미구현

### Future Improvements
- LLM API 연동
- Job Analysis 자동화
- Playwright / Selenium 기반 동적 페이지 수집
- 출처 신뢰도 평가
- 중복 검색 결과 제거 
- 여러 출처 통합 요약
- 지원자 관점 핵심 인사이트 생성

---

### Frontend

```bash
cd frontend
npm run dev
```

### Backend

#### OpenAI 환경 준비
프로젝트 루트에서 가상환경을 활성화하고 의존성을 설치합니다.

    source .venv/bin/activate
    python -m pip install -r requirements.txt

루트 `.env`에 다음 설정을 작성합니다.

    USE_MOCK=true
    LLM_PROVIDER=openai
    OPENAI_API_KEY=
    OPENAI_MODEL=

실제 API Key는 로컬 `.env`에만 입력합니다.
`.env.example`에는 실제 Key를 넣지 않습니다.

설정 테스트:

    python -m unittest discover -s backend/tests -p "test_*.py" -v

환경 로딩·검증과 클라이언트 생성 함수를 준비합니다.
현재 Job Analysis는 기존 mock을 사용하며 실제 OpenAI 요청은 하지 않습니다.

가상환경 실행 및 비활성화:
```bash
# 가상환경 실행
source .venv/bin/activate
# Python venv 비활성화
deactivate

# Conda 환경 비활성화
conda deactivate
```

```bash
uvicorn backend.app.main:app --reload
```

### GitHub 업로드

변경된 파일 확인:
```bash
git status
```
변경사항 스테이징:
```bash
git add .
```
커밋 생성:
```bash
git commit -m "update README"
```
GitHub에 업로드:
```bash
git push
```
