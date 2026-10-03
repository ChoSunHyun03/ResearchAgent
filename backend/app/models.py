from pydantic import BaseModel

# 사용자가 입력한 채용 공공
class JobInput(BaseModel):
    job_text: str

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
