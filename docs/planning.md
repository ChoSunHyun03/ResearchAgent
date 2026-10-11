# Company Research Agent

## 현재 개발 계획 — 2026-10-12 갱신

아래 Day 1~7 기록은 초기 MVP 개발 당시의 구현 상태입니다.
현재 기능은 README와 STEP 기록을 기준으로 확인합니다.

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

### 작업 방식

- AI Agent가 로컬 수정·테스트·문서 업데이트·commit·push를 수행합니다.
- 기존 `openai-enviroment` 브랜치를 사용하고 한 번에 하나의 STEP만 진행합니다.
- 단계 결과를 공유한 후 다음 STEP 요청을 기다립니다.
- 전체 코드 나열보다 구현 이유, 코드 흐름, 검증 결과를 설명합니다.
- 최초 STEP 설명에는 줄 번호를 생략하고, 오류 수정 요청에는 현재 파일의 정확한 위치를 안내합니다.
- 기존 기능을 유지하고 API Key를 코드·로그·Git에 포함하지 않습니다.

### STEP 8 범위 — 조사 이력과 결과 저장

- SQLite를 사용해 조사 실행 ID와 상태·시작 및 종료 시각·실패 원인을 저장
- 공고 분석·계획·검색 출처·최종 보고서 저장
- 실행 이력 목록과 상세 조회 API 제공
- 프론트엔드에서 이전 조사 결과 다시 열기
- 사용자가 명시적으로 확인한 선호 직무와 실행별 선택 직무 저장
- 지원 이력의 직무 빈도는 선택 제안에 활용하되 현재 요청을 덮어쓰지 않음
- 명시적 현재 선택 → 사용자가 확인한 저장 선호 → 선택 요청 순서
- 이력 없는 사용자도 직무 직접 입력·공고 후보 선택으로 진행
- 프로필 저장 범위와 사용자 식별 방식은 STEP 8 구현 시 명확히 구분
- 로그인, Vector DB, 검색 캐시는 이번 단계 범위에서 제외
- LangGraph 중단 지점 재개는 일반 결과 저장과 구분해 STEP 11에서 검토

---

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
- snippet 기반 Research Report
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
---
## STEP 2 — OpenAI Job Analysis

### 변경
- 환경설정에 따른 mock/OpenAI 분석 분기
- 기존 JobAnalysis를 Structured Outputs에 연결
- 입력·설정·외부 API·출력 오류 구분

### 검증
- 자동 테스트: 실행 후 기록
- 기존 mock 분석: 실행 후 기록
- 정상 공고: 실행 후 기록
- 필수조건 누락: 실행 후 기록
- 우대조건 누락: 실행 후 기록
- 매우 짧은 공고: 실행 후 기록
- 빈 입력: 실행 후 기록
- 실제 채용공고 대조: 실행 후 기록
---
## STEP 3 — LLM Research Planner

### 변경
- 별도 설정으로 LLM/규칙 기반 계획 전환
- 기존 ResearchPlan과 endpoint 유지
- 조사 항목 5~7개 제한
- 빈 항목과 동일 검색어 중복 검증
- 원본 회사명·직무명 유지
- 계획 재생성 시 이전 검색·보고서 초기화

### 검증
- 2026-10-12 백엔드 자동 테스트: 기존 18개 + 신규 9개, 총 27개 통과
- 2026-10-12 프론트엔드 `npm run build`: TypeScript 검사와 Vite build 통과
- 규칙 기반 모드 회귀: 자동 테스트 통과
- 실제 OpenAI 기반 AI Engineer / AX PM 계획 비교: 이번 작업에서 미실행
- 실제 검색을 포함한 계획→검색→보고서 연결: 이번 작업에서 미실행
- 자동 테스트는 외부 API를 mock 처리하므로 실제 모델 품질이나 접근 권한을 보장하지 않음
- 구현·자동 검증·문서 정리는 완료, 실제 API 품질 확인은 별도 검증 항목으로 유지

---
## STEP 4 — 검색 결과 정제와 평가용 예제 준비

### 구현 이유와 흐름

검색 결과 없음과 DDGS 실패가 모두 빈 배열이었던 문제를 해결합니다.
외부 서비스 오류가 있어도 성공한 다른 주제의 결과는 계속 활용합니다.

```text
React: 웹 리서치 시작
→ POST /api/research/search (기존 ResearchPlan)
→ run_web_research(): 주제별 반복
→ search_web(): 검색어 검증 → DDGS 후보 최대 6개
→ clean_search_results(): URL·공백 정리 → 무효 항목·주제 내 중복 제외 → 최대 3개
→ ResearchResult(results, status, error_kind, error_message)
→ WebResearch → React: 성공 결과 / 결과 없음 / 오류 표시
→ POST /api/research/report
→ create_research_report(): snippet·출처·검색 상태 전달
→ ResearchReport → React: 주제별 요약과 실패 안내
```

### 설계 결정

- 검색 성공 시 기존 `search_web()`의 리스트 반환을 유지하고 실패 시 SearchError를 발생시킴
- 기존 endpoint와 필드를 유지하고 상태 필드에 기본값을 두어 이전 요청도 수용
- 기존 상태 없는 요청은 기본 success로 읽으므로 과거 검색 실패 여부를 복원하지는 않음
- 같은 출처가 여러 조사 주제의 근거가 될 수 있어 중복 제거 범위는 주제 내부로 한정
- 추적 값과 fragment만 제거하고 경로 대소문자, 의미 있는 파라미터·인코딩·순서 유지
- 파라미터 순서가 다른 URL이나 내용이 비슷한 페이지까지 같은 것으로 판단하지 않음
- URL 정제는 페이지 수집의 내부 주소 접근 방어를 대체하지 않음; 수집 검증은 STEP 5에서 진행
- 검색 오류 원문을 출력하지 않고 안전한 오류 종류와 메시지를 주제별로 전달
- 전체 검색을 중단하지 않으므로 부분 실패도 HTTP 200, 실제 상태는 항목별로 확인
- 검색 재실행 시 이전 검색과 보고서 상태 초기화
- 연결 흐름 확인 중 발견한 보고서의 기업명 자리에 직무명이 표시되던 오류 수정

### 평가 예제

- 검색 정제 사례 4개: 추적 URL 중복, 무효·빈 항목, 순위·개수 제한, 빈 결과
- 직접 작성한 가상 공고 4개: AI Engineer, AX PM, 필수조건 누락, 회사·직무 누락
- 기대 분석은 검토 기준이며 표현과 키워드의 정확한 문자열 일치를 강제하지 않음
- 실제 기업 데이터나 정량 성능 점수로 소개하지 않음
- 모델 평가 실행기와 학습 데이터는 아직 추가하지 않음

### 검증 — 2026-10-12

- 백엔드 자동 테스트: 기존 27개 + 신규 13개, 총 40개 통과
- 프론트엔드 `npm run build`: TypeScript 검사 및 Vite build 통과
- 프론트엔드 `npm run lint`: 통과
- ASGI 요청 테스트: 검색 성공·빈 결과·timeout 혼합 → 보고서 반환 및 오류 상태 전달 확인
- 기존 상태 필드 없는 WebResearch 요청: 보고서 생성 호환 확인
- 실제 DDGS 단일 검색: `Python official documentation`, 결과 3개·고유 URL 3개 반환
- 실제 검색 한 건의 성공은 모든 공고의 검색 품질이나 지속적 서비스 가용성을 보장하지 않음
- 실제 OpenAI 호출과 화면 클릭 검증은 이번 작업에서 미실행

### 다음 단계

STEP 5에서 검색 결과 페이지 본문 수집을 구현합니다. 이번 STEP에는 포함하지 않습니다.

---
## STEP 5 — 검색된 페이지 본문 수집

### 목표와 설계 이유

검색 snippet보다 풍부한 근거를 다음 보고서 단계에 제공하기 위한 본문 수집입니다.
검색과 별도 실행해 기존 검색 응답 속도와 snippet 보고서 흐름을 유지합니다.
검색 성공과 페이지 접근 성공은 독립적으로 기록합니다.

### 코드와 데이터 흐름

```text
WebResearch (검색 결과와 주제별 검색 상태)
→ App.handleCollectSources(): loading, 이전 보고서 초기화
→ api.collectWebSources(): 기존 WebResearch를 JSON으로 전송
→ POST /api/research/collect
→ main.collect_research_sources(): Pydantic 검증된 객체 전달
→ research.collect_web_sources(): 입력을 복사하고 URL별로 순차 수집
   ├─ 같은 URL: 이번 요청의 캐시 결과 재사용
   ├─ 개수·시간 예산 도달: page.status=skipped
   └─ scraper.fetch_page()
       → validate_target(): HTTP(S)·포트·공개 DNS 주소 검증
       → 검증 IP에 직접 연결, HTTPS 원래 호스트 인증서·SNI 유지
       → 리다이렉트마다 재검증
       → 크기 제한 내 HTML/gzip 읽기
       → extract_html(): article → main → body 우선, 불필요 태그 제거
       → PageContent 또는 PageFetchError
→ SearchResult.page에 본문·시각·최종 URL·수집 상태 추가
→ WebResearch JSON 응답
→ App.setWebResearch(): 본문 펼치기 또는 실패·생략 메시지
→ 기존 /api/research/report: snippet 보고서 유지
```

### 유지하는 동작과 제한

- 기존 검색 결과와 `page` 없는 요청 지원, 수집하지 않아도 보고서 생성 가능
- 본문을 그대로 보고서 요약으로 사용하지 않음; 근거 기반 LLM 요약은 STEP 7
- 같은 URL은 요청 내에서 한 번 시도, 실패 결과도 요청 내 재사용; 영구 저장·캐시 없음
- 고유 URL 최대 10개, 페이지당 8초 예산, 전체 45초 진행 예산
- 연결·읽기 timeout 각각 최대 2초; OS DNS 조회는 강제 취소하지 않으므로 엄격한 종료 시간 보장은 아님
- 전송 및 gzip 해제 각각 1,000,000바이트 제한, 본문 최대 12,000자, 잘림 표시
- 공개 IP만 연결하고 자동 리다이렉트·자동 재시도·환경변수 프록시는 사용하지 않음
- 기본 검색 경로 정제와 별도로 실제 연결 주소를 검증하며 인증서 검증을 유지
- 기존 공고 URL 수집도 공통 수집기를 사용: `job_text` 문자열·20,000자 제한·실패 HTTP 400 유지
- 본문 추출은 HTML 구조에 따른 휴리스틱이며 로그인·JS 렌더링·PDF·기타 압축 형식 미지원
- 인터넷 전체의 수집 성공률이나 본문 정확성을 보장하지 않음

### 검증 — 2026-10-12

- 백엔드 테스트: 기존 40개 + 신규 24개, 총 64개 통과
- 프론트엔드 TypeScript·Vite build·lint 통과
- pip check: 의존성 충돌 없음; 이미 설치된 urllib3 2.8.0을 직접 의존성으로 명세
- 고정 HTML로 본문·제목 추출, 불필요 태그 제거, 본문 잘림 확인
- 내부·메타데이터 IP 및 공개/비공개 혼합 DNS 차단, 검증 IP 고정과 TLS 호스트 확인
- 리다이렉트 내부 주소 차단·횟수 제한, HTTP·timeout·크기·지원 형식·gzip 오류 검증
- 실제 HTTPS: https://www.python.org/about/ 본문 2,405자, 제목·UTC 수집 시각, 잘림 없음 확인
- 실제 페이지가 gzip을 반환해 제한된 gzip 해제 기능 추가 후 성공 확인
- 실제 OpenAI 호출 및 화면 클릭 검증은 이번 작업에서 미실행

### 다음 단계

STEP 6은 출처 유형과 관련성 분류입니다. 이번 작업에는 포함하지 않습니다.

---
## STEP 5 보완 — 전체 공고 수집과 지원 직무 선택

### 원인

SK브로드밴드 채용 안내 페이지는 article 4개가 있는데 첫 article만 수집해 69자를 반환했습니다.
main 전체에는 채용 제목과 지원자격이 있으므로 첫 article 우선 선택을 수정했습니다.
다만 HTML에 없는 직무별 상세 내용은 수집 범위를 늘려도 복원할 수 없습니다.

### 변경과 흐름

- main 전체 → 최상위 article 전체 → body 순서로 추출하고 head의 페이지 제목도 포함
- 짧은 공고 수집 결과에 warnings 추가, 기존 job_text 응답은 유지
- JobInput.target_position 선택적 추가, 기존 여섯 분석 필드를 유지하며 상태·후보·안내 추가
- 전체 공고에서 선택 없는 복수 직무는 needs_selection, 후보 버튼으로 같은 원문 재분석
- 상세 원문 없는 직무는 missing_details, 원문에 없는 일반 지식으로 보충하지 않음
- 단일 직무 또는 명시적 선택의 분석만 ready이며 해당 직무와 공통 지원자격만 추출하도록 지시
- 서버에서 선택/반환 직무 불일치, 채용 유형을 직무로 사용, 대기 상태의 혼합 정보 전달을 차단
- 해결 전 Research Plan 버튼과 서버의 계획 생성 모두 차단
- 입력 원문·지원 직무가 바뀌면 이전 분석·계획·검색·보고서 초기화
- 원래 결과 누락 테스트의 return_vaule 오타를 return_value로 수정하여 의도한 응답을 실제 검증

```text
URL 수집 → 전체 본문과 확인 안내 → React 원문 입력창
원문 + 선택적 지원 직무 → /api/jobs/analyze
→ OpenAI Structured Outputs → 서버 상태 보정
   ├─ 복수 직무, 선택 없음: 후보 표시 → 선택 → 같은 원문 재분석
   ├─ 상세 정보 없음: 상세 공고 입력 요청 → 계획 생성 차단
   └─ ready: 해당 직무 분석 → 기존 계획·검색·보고서 흐름
```

### DB 설계 반영

DB는 사용자 선호와 실행 이력을 기억하는 용도이며 처음 요청의 지원 직무를 알아내는 필수 조건은 아닙니다.
STEP 8에 확인한 선호 직무와 실행별 선택 직무 저장을 추가합니다.
현재 명시적 선택이 항상 우선하고, 이력은 추천 근거로만 사용합니다.
다른 직군 지원 가능성을 고려해 과거 이력만으로 현재 직무를 자동 선택하지 않습니다.
이번 작업에는 DB 구현이나 STEP 6을 포함하지 않습니다.

### 검증 — 2026-10-12

- 백엔드 기존 64개 + 신규 13개, 총 77개 통과
- 프론트엔드 TypeScript build 및 lint 통과
- 실제 해당 채용 페이지: 69자 → 2,067자, 채용 제목·지원자격·모집 분야 안내 확인
- 실제 OpenAI: 가상 복수 직무 공고에 선택 없이 needs_selection과 후보 두 개 반환
- 실제 OpenAI: AI Engineer 지정 시 모델 API 개발·Python·공통 학사 자격 반환, AX PM 조건 제외
- 실제 모델이 Junior Talent를 후보로 오분류한 사례를 확인해 서버 제외 규칙과 회귀 테스트 추가
- 보완 후 실제 채용 안내 페이지에 AI Engineer 지정: missing_details, 직무·조건 빈 값, 상세 공고 안내 확인
- 구조화 형식·대기 상태 처리는 검증했으나 모든 사이트·직무의 내용 정확성을 보장하지 않음
- 별도 JavaScript 데이터 수집이나 직무 상세 페이지 자동 탐색은 이번 범위에서 제외
