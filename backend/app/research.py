import json
from pathlib import Path

from backend.app.models import JobAnalysis

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
    """

    pass