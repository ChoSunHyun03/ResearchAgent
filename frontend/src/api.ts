const API_BASE_URL = "http://localhost:8000";

// 백엔드 서버가 정상적으로 실행 중인지 확인하는 함수
// async 함수이기 때문에 내부에서 await를 사용할 수 있음
export async function checkHealth() {
     // fetch()를 사용해 FastAPI의 /health API로 GET 요청을 보냄
    // `${}` 문법을 사용하기 위해 문자열을 백틱(`)으로 감싸야 함
    // 실제 요청 주소 : http://localhost:8000/health
    const response = await fetch(`${API_BASE_URL}/health`);

    if (!response.ok){
        throw new Error("Backend 연결에 실패했습니다.");
    }
    return response.json();
}

export async function analyzeJob(jobText: string) {
    const response = await fetch(
        `${API_BASE_URL}//api/jobs/analyze`,
        {
            method: "POST",
            headers: {
                "Content-Type": 'application/json',
            },

            body: JSON.stringify({
                job_text: jobText,
            }),
        }
    );

    if (!response.ok) {
        throw new Error("채용공고 분석에 실패했습니다.");
    }

    return response.json();
}