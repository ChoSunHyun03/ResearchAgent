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

---

## Day 5 - Research Report

### 목표

Web Research 결과를 기반으로
지원자가 기업 및 직무 조사에 활용할 수 있는
Research Report를 생성한다.

### Workflow

WebResearch
→ create_research_report()
→ ResearchReport
→ ReportSection
→ Frontend 출력

### Report 구성

각 Report Section은 다음 정보를 포함한다.

- topic
- 검색 Query
- 검색 결과 기반 핵심 내용
- 출처

### 현재 구현 방식

LLM API를 사용하지 않기 때문에
웹 검색 결과의 snippet을 기반으로
주제별 정보를 구조화하여 Report를 생성한다.

검색 결과에 존재하지 않는 내용을
임의로 생성하지 않는다.

### 현재 한계

현재 Report는 검색 결과를 구조화하는 수준이며,
여러 출처를 종합한 자연어 요약이나
지원자 관점의 인사이트 생성은 수행하지 않는다.

### 추후 개선

LLM API 연결 시 다음 기능을 추가한다.

- 여러 출처의 내용 통합 요약
- 중복 정보 제거
- 신뢰도 높은 출처 우선 정리
- 지원 직무와 연결된 핵심 인사이트 생성
- 지원동기 및 면접 준비에 활용 가능한 정보 추출

---

## Day 6 - Input & UX Improvement

### 목표

기존 Research Agent Workflow를
실제 사용 가능한 형태로 개선한다.

### 주요 구현

- 채용공고 URL 입력 기능 추가
- URL 페이지 텍스트 추출
- 직접 텍스트 입력 방식 유지
- 검색 결과가 없는 경우 예외 처리
- 사용자 친화적인 Research Topic 이름 적용
- 기본 UI 구조 개선

### URL Workflow

Job Posting URL
→ requests
→ BeautifulSoup
→ Text Extraction
→ Job Analysis

### Fallback

일부 채용사이트는 JavaScript 기반으로
본문을 렌더링하기 때문에
requests 방식으로 내용을 가져오지 못할 수 있다.

이 경우 사용자가 채용공고 텍스트를
직접 입력할 수 있도록 기존 입력 방식을 유지한다.

### UX Improvement

- API 요청 중 loading 상태 표시
- API 단계별 error message 적용
- 검색 결과가 없는 경우 별도 메시지 출력
- Research Topic 이름을 사용자 친화적인 한글로 변환
- 각 기능 영역을 section 단위로 분리

### 현재 한계

- JavaScript 기반 동적 페이지 수집 제한
- 로그인 필요 페이지 수집 불가
- 사이트별 HTML 구조 최적화 미적용
- 현재 Job Analysis는 Mock Data 기반

### 추후 개선

- Playwright 또는 Selenium 적용
- 채용사이트별 Parser 구현
- 실제 LLM API 연동
- 검색 결과 신뢰도 평가
- 여러 출처 기반 통합 요약

## Day 7 - Evaluation & Documentation

### 목표

1주 동안 개발한 Company Research Agent MVP를
최종 테스트하고 프로젝트 구조와 한계점을 정리한다.

### Final Workflow

Job Posting URL / Text
→ Job Analysis
→ Research Plan
→ Web Research
→ Research Report

### Test Cases

#### 정상 URL

URL에서 페이지 텍스트를 추출하고
기존 Research Workflow까지 정상적으로 연결되는지 확인.

#### 직접 텍스트 입력

URL 수집이 불가능한 경우에도
사용자가 직접 채용공고를 입력해
전체 Workflow를 사용할 수 있는지 확인.

#### 잘못된 URL

잘못된 URL 입력 시
서버가 종료되지 않고 사용자에게
에러 메시지를 제공하는지 확인.

#### 검색 결과 없음

웹 검색 결과가 없더라도
빈 리스트를 반환하고 전체 Workflow가
중단되지 않는지 확인.

### MVP 결과

채용공고 입력부터 기업 리서치 결과 생성까지
하나의 End-to-End Workflow를 구현했다.

### 현재 한계

- 실제 LLM API 미연동
- Job Analysis Mock 기반
- 동적 페이지 수집 제한
- 검색 snippet 기반 Report
- 출처 신뢰도 평가 미구현

### 향후 개선 방향

- 실제 LLM 기반 Job Analysis
- Research Query 자동 생성
- 검색 결과 통합 요약
- 출처 신뢰도 점수화
- 사용자 경험 기반 Research Insight 생성
---
## STEP 1 — OpenAI 환경 구성

### 범위

- 백엔드 의존성 명세 작성
- 프로젝트 루트 `.env` 로딩
- 시스템 환경변수 우선 적용
- Key·모델 설정 검증
- OpenAI 클라이언트 생성 함수 분리
- 외부 API 호출 없이 환경설정 테스트

### 유지하는 기능

- 기존 FastAPI endpoint
- 기존 mock Job Analysis
- 규칙 기반 Research Plan
- DDGS 검색
- snippet 기반 Research Repodrt
- 기존 프론트엔드

### 아직 구현하지 않은 기능

- 실제 OpenAI Job Analysis
- LLM Research Planning 및 Report 요약
- Ollama Provider
- LangGraph 및 MCP

### 검증 기록

- 환경설정 테스트: 실행 후 결과 기록
- health endpoint: 실행 후 결과 기록
- 기존 mock 분석: 실행 후 결과 기록