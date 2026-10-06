from fastapi import FastAPI,HTTPException
# React와 FastAPI가 서로 다른 주소(port)를 사용할 때 브라우저가 API 요청을 허용할 수 있도록 CORS 설정
from fastapi.middleware.cors import CORSMiddleware

from backend.app.models import (
    JobInput,
    JobUrlInput, 
    JobAnalysis, 
    ResearchPlan,
    WebResearch,
    ResearchReport,)

from backend.app.research import (
    analyze_job, 
    create_research_plan,
    run_web_research,
    create_research_report,)

from backend.app.scraper import fetch_job_posting

# FastAPI 애플리케이션 생성 -> 앞으로 API들은 모두 이 app에 등록
app = FastAPI(
    title="Company Research Agent API",
    version= "0.1.0",
)

# React는 localhost:5173,
# FastAPI는 localhost:8000에서 실행되기 때문에
# React가 FastAPI에 요청할 수 있도록 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173",
                   "http://localhost:5174"],
    allow_credentials=True,  # 쿠키나 인증 정보 등을 포함한 요청을 허용
    allow_methods=["*"], # GET, POST, PUT, DELETE 등 모든 HTTP Method 허용
    allow_headers=['*'], # 모든 HTTP Header 허용
)

@app.get("/health")
def health_check():
    return{
        "status":"ok",
        "message":"Company Research Agent API is runnung"
    }


@app.post("/api/jobs/analyze", response_model=JobAnalysis)
def analyze_job_posting(job: JobInput):
    """
    프론트엔드에서 전달받은 채용공고를 분석한다. 
    """
    return analyze_job(job.job_text)

@app.post("/api/research/plan", response_model=ResearchPlan)
def generate_research_plan(job_analysis: JobAnalysis):
    """
    채용공고 분석 결과를 기반으로
    기업 및 직무 Research Plan을 생성
    """
    return create_research_plan(job_analysis)

@app.post("/api/research/search",response_model=WebResearch)
def search_research_plan(research_plan: ResearchPlan):
    """
    Research Plan을 기반으로 실제 웹 검색을 수행한다.
    """

    return run_web_research(research_plan)

@app.post("/api/research/report",response_model=ResearchReport)
def generate_research_report(web_research: WebResearch):
    """
    웹 검색 결과를 받아
    최종 Research Report를 생성한다.
    """

    return create_research_report(web_research)

@app.post("/api/jobs/fetch")
def fetch_job_posting_api(job:JobUrlInput):
    """
    채용공고 URL을 받아
    웹페이지의 텍스트 내용을 반환한다.
    """
    try: 
        # HttpUrl 객체를 문자열로 반환
        job_text = fetch_job_posting(
            str(job.job_url)
        )

        return {"job_text": job_text}
    except ValueError as error:
        # scraper.py에서 URL 접근 실패가 발생한 경우 
        # 서버 내부 오류 500 대신
        # 잘못된 요청이라는 의미의 400 응답을 반환
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )