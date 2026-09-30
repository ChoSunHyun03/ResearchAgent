from fastapi import FastAPI
# React와 FastAPI가 서로 다른 주소(port)를 사용할 때 브라우저가 API 요청을 허용할 수 있도록 CORS 설정
from fastapi.middleware.cors import CORSMiddleware

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

