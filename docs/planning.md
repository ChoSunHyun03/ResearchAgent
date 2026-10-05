# Company Research Agent

## 프로젝트 배경

기업에 지원할 때 채용공고를 확인한 뒤
기업 홈페이지, 최근 뉴스, 주요 사업, 기술 방향,
직무 정보를 여러 사이트에서 반복적으로 조사해야 한다.

기업마다 비슷한 조사 과정을 반복하면서
시간이 많이 소요되고 조사 결과의 형식도 일정하지 않다.

## 문제 정의

채용공고를 기반으로 지원에 필요한 기업 및 직무 정보를
직접 탐색하고 정리하는 반복적인 리서치 업무를 줄인다.

## 프로젝트 목표

채용공고를 입력하면 AI가 공고를 분석하고,
추가로 조사해야 할 내용을 계획한 뒤,
관련 정보를 검색해 출처 기반 Research Report를 생성한다.

## Workflow

채용공고 입력
→ 채용공고 분석
→ Research Plan 생성
→ Web Search
→ Source 분석
→ Report 생성

## MVP 기능

1. 채용공고 입력
2. 기업명 / 직무 / 업무 / 요구사항 추출
3. Research Query 생성
4. Web Search
5. 정보 추출
6. Research Report 생성
7. 출처 표시

## MVP 제외 기능

- 로그인
- 회원가입
- Vector DB
- RAG
- LangGraph
- Multi-Agent
- 자소서 자동 생성
- 기업 비교

## 기술 스택

Frontend
- React
- TypeScript
- Vite

Backend
- Python
- FastAPI
- Pydantic

AI
- LLM API

Search
- Web Search API

---

## Day 1 - Project Setup

### 목표
React + FastAPI 개발 환경 구성 및 통신 확인

### 구현
- React + TypeScript + Vite 세팅
- FastAPI 세팅
- `/health` API 생성
- Frontend ↔ Backend 통신 확인
- Git / GitHub 연결

---

## Day 2 - Job Posting Analyzer

### 목표

채용공고 텍스트를 입력하면
구조화된 JobAnalysis 결과를 반환한다.

### 현재 구현 방식

LLM API 비용 문제로 실제 API 호출 대신
별도의 Mock JSON 데이터를 사용한다.

Mock 데이터는 실제 서비스 데이터와 분리하여
`mock_data/` 폴더에 저장한다.

해당 폴더는 GitHub에는 업로드하지 않으며,
데이터 구조를 확인할 수 있도록
`mock_data.example.json`만 Repository에 포함한다.

### Workflow

React
→ FastAPI
→ analyze_job()
→ Mock JSON
→ JobAnalysis
→ React Result

### 분석 항목

- 회사명
- 직무명
- 주요 업무
- 필수 역량
- 우대사항
- 핵심 키워드

### 추후 개선

Mock 데이터 대신 LLM API를 연결하여
실제 채용공고를 동적으로 분석하도록 변경한다.
---

## Day 3 - Research Planner

### 목표

JobAnalysis 결과를 기반으로
지원자가 추가로 조사해야 할 기업 및 직무 정보를 정의하고
검색 Query를 생성한다.

### Workflow

JobAnalysis
→ create_research_plan()
→ ResearchPlan
→ ResearchQuery
→ Frontend 출력

### Research Query 구성

- topic: 조사 분야
- query: 실제 검색에 사용할 검색어
- reason: 해당 정보를 조사해야 하는 이유

### 현재 구현 방식

LLM API 대신 회사명, 직무명, 핵심 키워드를 이용해
규칙 기반으로 Research Query를 생성한다.

### 현재 Research Topic

- 회사 주요 사업
- 지원 직무
- 핵심 기술
- 최근 뉴스
- 기업 전략

### 다음 단계

Day 4에서 생성된 Research Query를 실제 웹 검색과 연결하고,
채용공고 URL에서 본문을 가져오는 방식도 함께 검토한다.

---

## Day 4 - Web Research

### 목표

Day 3에서 생성한 Research Query를
실제 웹 검색과 연결한다.

### Workflow

ResearchPlan
→ ResearchQuery
→ Web Search
→ SearchResult
→ WebResearch
→ Frontend 출력

### 검색 결과 구성

- title
- url
- snippet

### 구현 방식

외부 유료 Search API 대신
API Key 없이 사용할 수 있는 DDGS 기반 검색을 사용한다.

각 Research Query당 최대 3개의 검색 결과를 수집한다.

### 현재 한계

검색 결과의 제목, URL, 요약만 수집하며
각 웹페이지의 본문 전체는 아직 분석하지 않는다.

### 다음 단계

Day 5에서 검색 결과를 기반으로
지원자가 활용할 수 있는 Research Report를 생성한다.