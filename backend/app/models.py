from pydantic import BaseModel, HttpUrl

# 사용자가 입력한 채용 공공
class JobInput(BaseModel):
    job_text: str

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

# 하나의 웹 검색 결과
class SearchResult(BaseModel) :
    title : str
    url : str
    snippet : str

# 하나의 Research Query에 대한 검색 결과
class ResearchResult(BaseModel) :
    topic : str
    query : str
    reason : str
    results : list[SearchResult]

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

# 최종 Research Report
class ResearchReport(BaseModel) : 
    company : str
    position : str
    sections : list[ReportSection]
