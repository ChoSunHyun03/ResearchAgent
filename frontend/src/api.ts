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
        `${API_BASE_URL}/api/jobs/analyze`,
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
        throw new Error("채용공고 분석에 실패했습니다. 입력 데이터와 Backend 상태를 확인해주세요");
    }

    return response.json();
}

export async function createResearchPlan(jobAnalysis: object) {
    const response =  await fetch(
        `${API_BASE_URL}/api/research/plan`,
        {
            method : "POST",
            headers : {
                "Content-Type" : "application/json",
            },
            body: JSON.stringify(jobAnalysis),
        }
    );

    if(!response.ok){
        throw new Error("Research Plan 생성에 실패했습니다.");
    }

    return response.json();
}

export async function runWebResearch(researchPlan: object) {
    const response = await fetch(
        `${API_BASE_URL}/api/research/search`,
        {
            method: "POST",

            headers:{
                "Content-Type": "application/json",
            },

            body: JSON.stringify(researchPlan),
        }
    );

    if(!response.ok){
        throw new Error("웹 검색 중 오류가 발생했습니다. 일부 검색어에서 결과가 없거나 검색 서비스 연결에 실패했을 수 있습니다.");
    }
    
    return response.json();
}

// Web Research 결과를 Bckend로 전달 -> 최종 Research Report 생성
export async function createResearchReport(webResearch: object) {
    const response = await fetch(
        `${API_BASE_URL}/api/research/report`,
        {
            method : "POST",

            headers:{
                "Content-Type": "application/json",
            },

            body: JSON.stringify(webResearch),
        }
    );

    if (!response.ok){
        throw new Error("Research Report 생성에 실패했습니다.");
    }

    return response.json();
}

// 채용공고 URL을 Backend로 전달하여
// 페이지의 텍스트 내용을 가져오는 함수
export async function fetchJobPosting(jobUrl : string) {
    const response = await fetch(
        `${API_BASE_URL}/api/jobs/fetch`,
        {
            method : "POST",

            headers : {
                "Content-Type" : "application/json",
            },

            body : JSON.stringify({
                job_url: jobUrl,
            }),
        }
    );

    if (!response.ok) {
        throw new Error("채용공고 URL을 불러오지 못했습니다.");
    }

    return response.json();
}