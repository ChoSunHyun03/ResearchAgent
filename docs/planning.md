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