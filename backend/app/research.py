import json
import time
from pathlib import Path

from backend.app.models import (
    PageContent,
    JobAnalysis, 
    ResearchPlan, 
    ResearchQuery,
    ResearchResult,
    WebResearch,
    ResearchReport,
    ReportSection,
    ReportSource,)

from backend.app.search import SearchError, normalize_url, search_web
from backend.app.scraper import PAGE_SECONDS, PageFetchError, fetch_page

from backend.app.config import load_settings

# OpenAI 호출은 별도 Provider에 맡김
from backend.app.llm.openai_provider import(
    JobAnalysisError,
    analyze_job_with_openai,
)

from backend.app.llm.research_planner import (
    create_research_plan_with_openai,
)

"""
# 지금은 실제 OpenAI API를 호출하지 않고 Mock 데이터를 사용
USE_MOCK = True
"""

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


def analyze_job(job_text: str, target_position: str = "") -> JobAnalysis:
    """
    채용공고를 분석.

    입력을 검증하고 설정에 따라
    mock 또는 OpenAI로 분석합니다.
    """

    # 공백만 있는 입력도 실제 호출 전에 차단
    cleaned_text = job_text.strip()

    if not cleaned_text:
        raise ValueError("채용공고 내용을 입력해주세요.")

    # 현재 URL 수집기의 길이 제한과 동일하게 맞춤
    # 직접 입력은 조용히 자르지 않고 오류로 안내
    if len(cleaned_text) > 20000:
        raise ValueError("채용공고는 20,000자 이하로 입력해주세요.")

    selected_position = target_position.strip()
    if len(selected_position) > 120:
        raise ValueError("지원 직무는 120자 이하로 입력해주세요.")
    settings = load_settings()

    if settings.use_mock:
        try:
            # 기존 개발용 분석을 유지
            return finalize_job_analysis(load_mock_analysis("interx.json"), selected_position)
        except (OSError, ValueError):
            raise JobAnalysisError(
                "mock_data",
                "mock 분석 파일의 위치와 JSON 구조를 확인해주세요.",
            ) from None

    # 실패하면 오류를 반환하며 mock으로 자동 전환하지 않음
    if selected_position:
        result = analyze_job_with_openai(cleaned_text, settings, selected_position)
    else:
        result = analyze_job_with_openai(cleaned_text, settings)
    return finalize_job_analysis(result, selected_position)


def finalize_job_analysis(result: JobAnalysis, target_position: str = "") -> JobAnalysis:
    """여러 직무를 섞지 않고 선택·상세 정보 대기 상태를 서버에서도 지킵니다."""
    key = lambda value: "".join(value.split()).casefold()
    # 채용 유형은 지원 직무 후보가 아닙니다. 흔한 오분류를 서버에서 제외합니다.
    non_roles = {key(value) for value in ("Junior Talent", "신입", "신입사원", "신입 채용",
        "신입사원 채용", "경력", "인턴", "채용", "모집 분야", "전체 채용", "주니어 탤런트")}
    candidates = list(dict.fromkeys(value.strip() for value in result.available_positions
        if value.strip() and key(value) not in non_roles))
    status = result.analysis_status
    message = result.analysis_message
    target = target_position.strip()
    if len(candidates) > 1 and not target:
        status = "needs_selection"
        message = "여러 직무가 포함되어 있습니다. 지원 직무를 선택한 뒤 다시 분석해주세요."
    elif target:
        # 사용자가 지정한 직무와 모델이 반환한 직무가 다르면 진행하지 않습니다.
        known = candidates or ([result.position] if result.position and key(result.position) not in non_roles else [])
        if not known:
            status = "missing_details"
            message = message or "선택할 모집 직무와 상세 내용을 찾지 못했습니다. 해당 직무의 상세 공고를 추가해주세요."
        elif key(target) not in {key(value) for value in known}:
            status = "needs_selection"
            message = "지원 직무를 공고에서 확인하지 못했습니다. 표시된 직무명을 선택하거나 상세 공고를 추가해주세요."
        elif status == "ready" and key(result.position) != key(target):
            status = "missing_details"
            message = "선택한 직무의 상세 내용을 확인하지 못했습니다. 상세 공고를 추가해주세요."
    if status == "needs_selection" and not candidates and not result.position.strip():
        status = "missing_details"
        message = "모집 직무 목록을 찾지 못했습니다. 상세 공고를 추가해주세요."
    if key(result.position) in non_roles:
        status = "missing_details"
        message = "채용 유형만 확인되고 지원 직무가 없습니다. 직무별 상세 공고를 추가해주세요."
    if status == "ready" and not result.position.strip():
        status = "missing_details"
        message = "모집 직무를 확인할 수 없습니다. 지원 직무와 상세 공고를 입력해주세요."
    if status != "ready":
        # 대기 상태에서는 다른 직무의 업무·조건을 화면과 Planner로 전달하지 않습니다.
        return result.model_copy(update={"position": "", "responsibilities": [], "requirements": [],
            "preferred": [], "keywords": [], "competencies": [], "available_positions": candidates,
            "analysis_status": status, "analysis_message": message or "지원 직무의 상세 공고를 확인해주세요."})
    return result.model_copy(update={"available_positions": candidates})


def create_research_plan(job_analysis: JobAnalysis) -> ResearchPlan:
    """
    설정에 따라 LLM 또는 기존 규칙 기반 계획을 생성합니다.
    """

    if job_analysis.analysis_status != "ready":
        raise ValueError("지원 직무를 선택하고 상세 공고를 분석한 뒤 계획을 생성해주세요.")

    # 대상이 불명확한 상태로 다른 회사 정보를 조사하지 않게 주의
    # 누락 시 공고를 보완하고 다시 분석 
    if(
        not job_analysis.company.strip()
        or not job_analysis.position.strip()
    ) : 
        raise ValueError(
            "회사명과 직무명이 있는 분석 결과가 필요합니다."
        )

    settings = load_settings()

    # LLM 플래너가 꺼져 있으면 기존 규칙 기반 계획을 생성
    if not settings.use_llm_planner:
        return create_rule_based_research_plan(job_analysis)

    # LLM 플래너가 켜져 있으면 openAI로 계획을 생성
    return create_research_plan_with_openai(job_analysis, settings)

def create_rule_based_research_plan(job_analysis: JobAnalysis) -> ResearchPlan:
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
        # 실패는 해당 주제에 기록하고 다음 주제의 검색을 계속합니다.
        status = "success"
        error_kind = None
        error_message = None
        try:
            results = search_web(research_query.query, max_results=3)
            if not results:
                status = "no_results"
        except SearchError as error:
            results = []
            status = "error"
            error_kind = error.kind
            error_message = str(error)
        except ValueError:
            results = []
            status = "error"
            error_kind = "invalid_query"
            error_message = "검색어와 검색 결과 개수를 확인해주세요."

        research_results.append(
            ResearchResult(
                topic=research_query.topic,
                query=research_query.query,
                reason=research_query.reason,
                results=results,
                status=status,
                error_kind=error_kind,
                error_message=error_message,
            )
        )

    return WebResearch(
        company=research_plan.company,
        position=research_plan.position,
        research_results=research_results,
    )

def collect_web_sources(web_research: WebResearch) -> WebResearch:
    """요청 안에서 URL별로 한 번 수집하고 기존 검색 결과에 본문을 붙입니다."""
    collected = web_research.model_copy(deep=True)
    cache: dict[str, PageContent] = {}
    deadline = time.monotonic() + 45
    for research_result in collected.research_results:
        for result in research_result.results:
            key = normalize_url(result.url) or result.url
            if key in cache:
                result.page = cache[key].model_copy(deep=True)
                continue
            remaining = deadline - time.monotonic()
            if len(cache) >= 10 or remaining <= 0:
                result.page = PageContent(status="skipped", error_kind="budget",
                    error_message="이번 요청의 수집 개수 또는 시간 제한에 도달했습니다.")
                continue
            try:
                page = fetch_page(key, seconds=min(PAGE_SECONDS, remaining))
            except PageFetchError as error:
                page = PageContent(status="error", error_kind=error.kind, error_message=str(error))
            cache[key] = page
            result.page = page.model_copy(deep=True)
    return collected


def create_research_report(web_research: WebResearch) -> ResearchReport:
    """
    WebResearch 결과를 기반으로 최종 Research Report를 생성

    현재 LLM API를 사용하지 않기 때문에 
    검색 결과를 snippet을 그대로 핵심 내용으로 활용
    """

    sections = []

    for research_result in web_research.research_results:
        summary = []
        sources = []

        # 하나의 Query에 대한 검색 결과를 순회
        for search_result in research_result.results:

            # 하나의 결과에 snippet이 존재하는 경우에만 추가
            if search_result.snippet:
                summary.append(search_result.snippet)

            # 제목이나 URL이 있는 경우 출처로 저장
            if search_result.title or search_result.url:
                sources.append(
                    ReportSource(
                        title = search_result.title,
                        url = search_result.url,
                    )
                )

        # 하나의 Topic에 대한 Report Section 생성
        section = ReportSection(
            topic = research_result.topic,
            query = research_result.query,
            summary = summary,
            sources = sources,
            status=research_result.status,
            error_kind=research_result.error_kind,
            error_message=research_result.error_message,
        )

        # 전체 Report Section 목록에 추가
        sections.append(section)

    # 최종 Research Report
    return ResearchReport(
        company = web_research.company,
        position = web_research.position,
        sections = sections,
    )