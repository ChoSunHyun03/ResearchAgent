from pydantic import BaseModel

# 프론트엔드에서 채용공고 텍스트를 전달받을 때 사용하는 입력 모델
class JobInput(BaseModel):
    job_text: str

# 채용공고  분석 결과의 구조를 정의하는 모델
class JobAnalysis (BaseModel):
    company : str
    position : str
    responsibilities : list[str]
    requirements : list[str]
    preferred : list[str]
    keywords : list[str]