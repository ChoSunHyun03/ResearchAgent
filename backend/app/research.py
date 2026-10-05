import json
from pathlib import Path

from backend.app.models import (
    JobAnalysis, 
    ResearchPlan, 
    ResearchQuery,
    ResearchResult,
    WebResearch,)

from backend.app.search import search_web

# 지금은 실제 OpenAI API를 호출하지 않고 Mock 데이터를 사용
USE_MOCK = True

# 프로젝트 루트 위치
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# MOCK 데이터 폴더
MOCK_DATA_DIR = PROJECT_ROOT / "mock_data"


def load_mock_analysis(file_name: str) -> JobAnalysis:
    """
    mock_data 폴더에 저장된 JSON 파일을 읽어서
    JobAnalysis 객체로 변환한다.
    """
    file_path = MOCK_DATA_DIR / file_name

    # JSON 파일 읽기
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    # JSON 데이터를 JobAnalysis 모델로 변환
    return JobAnalysis(**data)


def analyze_job(job_text: str) -> JobAnalysis:
    """
    채용공고를 분석.

    현재는 Mock 데이터를 반환하고,
    추후 LLM API 호출 방식으로 교체한다.
    """

    if USE_MOCK:
        return load_mock_analysis("interx.json")

def create_research_plan(job_analysis):
    """
    공고 분석 결과를 기반으로 
    어떤 내용을 조사할 지 Research Plan을 생성

    현재는 LLM 없이 규칙 기반으로 Query를 생성
    """

    company = job_analysis.company
    position = job_analysis.position

    # 공고에서 추출한 주요 키워드 중 앞의 3개 사용
    keyword_text = " ".join(job_analysis.keywords[:3])

    queries = [
        ResearchQuery(
            topic = "company_business",
            query = f"{company} 주요 사업",
            reason = "회사가 어떤 사업을 중심으로 운영되는지 파악하기 위해"
        ),

        ResearchQuery(
            topic = "job_role",
            query = f"{company} {position} 직무 업무",
            reason = "채용공고에서 강조한 기술이 회사에서 어떻게 활용되는지 파악하기 위해"
        ),

        ResearchQuery(
            topic = "technology",
            query = f"{company} {keyword_text}",
            reason = "채용공고에서 강조한 기술이 회사에서 어떻게 활용되는지 파악하기 위해"
        ),    

        ResearchQuery(
            topic = "recent_news",
            query = f"{company} 최근 뉴스 {keyword_text}",
            reason = "회사의 최근 사업 방향과 주요 이슈를 파악하기 위해"
        ),

        ResearchQuery(
            topic = "company_strategy",
            query = f"{company} AI 디지털전환 전략",
            reason = "회사의 기술 및 디지털 전환 방향을 파악하기 위해"
        ),
    ]

    return ResearchPlan(
        company = company,
        position = position,
        queries = queries
    )

def run_web_research(research_plan: ResearchPlan) -> WebResearch:
    """
    Research Plan의 각 Query를 실제 웹 검색과 연결한다.
    """

    research_results = []

    for research_query in research_plan.queries:
        results = search_web(
            research_query.query,
            max_results = 3,
        )

        research_results.append(
            ResearchResult(
                topic=research_query.topic,
                query=research_query.query,
                reason=research_query.reason,
                results=results,
            )
        )

    return WebResearch(
        company=research_plan.company,
        position=research_plan.position,
        research_results=research_results,
    )