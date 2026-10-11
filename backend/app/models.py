from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl

# 사용자가 입력한 채용 공공
class JobInput(BaseModel):
    job_text: str
    target_position: str = Field(default="", max_length=120)

# 채용공고 URL 입력
class JobUrlInput(BaseModel):
    # HttpUrl을 사용하면 잘못된 URL 형식을 FastAPI가 자동 검증함
    job_url : HttpUrl

# 채용공고 분석 결과
class JobAnalysis (BaseModel):
    company : str
    position : str
    responsibilities : list[str]
    requirements : list[str]
    preferred : list[str]
    keywords : list[str]
    # 기존 여섯 필드는 유지하고 분석의 진행 가능 여부를 추가합니다.
    analysis_status: Literal["ready", "needs_selection", "missing_details"] = "ready"
    available_positions: list[str] = Field(default_factory=list)
    analysis_message: str = ""

# 하나의 리서치 항목
class ResearchQuery (BaseModel) :
    # 조사 분야
    topic : str

    # 실제 검색에 사용할 검색어
    query : str

    # 이 내용을 조사해야 되는 이유
    reason : str

# 전체 Research Plan
class ResearchPlan (BaseModel) : 
    company : str
    position : str

    # 여러 개의 ResearchQuery를 저장
    queries : list[ResearchQuery]

# 검색 상태와 별도로 페이지별 본문 수집 상태를 보관합니다.
class PageContent(BaseModel):
    status: Literal["success", "error", "skipped"]
    final_url: str = ""
    title: str = ""
    text: str = ""
    truncated: bool = False
    fetched_at: datetime | None = None
    error_kind: Literal["unsafe_url", "network", "timeout", "redirect", "http", "unsupported", "too_large", "empty_content", "budget"] | None = None
    error_message: str | None = None

# 하나의 웹 검색 결과
class SearchResult(BaseModel) :
    title : str
    url : str
    snippet : str
    page: PageContent | None = None

# 기존 필드를 유지하면서 검색 상태를 추가합니다.
SearchStatus = Literal["success", "no_results", "error"]
SearchErrorKind = Literal["timeout", "rate_limit", "upstream", "invalid_response", "invalid_query"]

# 하나의 Research Query에 대한 검색 결과
class ResearchResult(BaseModel) :
    topic : str
    query : str
    reason : str
    results : list[SearchResult]
    status: SearchStatus = "success"
    error_kind: SearchErrorKind | None = None
    error_message: str | None = None

# 전체 웹 리서치 결과
class WebResearch(BaseModel) :
    company : str
    position : str 
    research_results : list[ResearchResult]

# Research Report에서 사용할 하나의 출처 정보
class ReportSource(BaseModel) :
    title : str
    url : str

# 하나의 Research Topic을 정리한 Report Section
class ReportSection(BaseModel) : 
    topic : str
    query : str
    summary : list[str]
    sources : list[ReportSource]
    # 보고서에서도 실패한 검색을 단순한 정보 부족으로 숨기지 않습니다.
    status: SearchStatus = "success"
    error_kind: SearchErrorKind | None = None
    error_message: str | None = None

# 최종 Research Report
class ResearchReport(BaseModel) : 
    company : str
    position : str
    sections : list[ReportSection]
