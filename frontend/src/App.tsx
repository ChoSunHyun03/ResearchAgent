import {useState} from "react";
// api.ts에서 만든 analyzeJob 함수를 가져옴
import {analyzeJob, createResearchPlan } from "./api";

interface JobAnalysis {
  company: string;
  position: string;
  responsibilities: string[];
  requirements: string[];
  preferred: string[];
  keywords: string[];
}

interface ResearchQuery{
  topic: string;
  query: string;
  reason: string;
}

interface ResearchPlan {
  company: string;
  position: string;
  queries: ResearchQuery[];
}


// React의 메인 컴포넌트
// 현재 화면에 표시되는 UI를 담당함
function App() {
  const [jobText, setJobText] = useState("");
  const [result, setResult] = useState<JobAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [researchPlan, setResearchPlan] = useState<ResearchPlan | null>(null);

  const handleAnalyze = async() => {
    try{
      setLoading(true);
      setError("");
      setResult(null);
      setResearchPlan(null);

      const data = await analyzeJob(jobText);

      setResult(data);

    } catch{
      setError("채용공고 분석에 실패했습니다.");

    } finally{
      setLoading(false);
    }
  };

  const handleCreateResearchPlan = async() => {
    if (!result) {
      return;
    }

    try {
      setLoading(true);
      setError("");

      const plan = await createResearchPlan(result);
      setResearchPlan(plan);

    } catch {
      setError("Research Plan 생성에 실패했습니다.");
    
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <h1>
        Company Research Agent
      </h1>
      <p>
        채용공고를 입력하면 기업과 직무 정보를 분석합니다.
      </p>

      <textarea
        rows={15}
        cols={80}
        value={jobText}
        onChange={(event) => setJobText(event.target.value)}
        placeholder="채용공고 내용을 입력하세요"
      />

      <br />
      
      <button
        onClick={handleAnalyze}
        disabled={!jobText || loading}
        >
          {loading ? "분석 중..." : "채용공고 분석"}
        </button>

        {error && <p>{error}</p>}

        {result && (
          <section>
            <h2>분석 결과</h2>

            <p>
              <strong>회사:</strong> {result.company}
            </p>
            <p>
              <strong>직무:</strong> {result.position}
            </p>

            <h3>주요 업무</h3>
            <ul>
              {result.responsibilities.map((item, index) => (
                <li key={index}>{item}</li>
              ))}
            </ul>
      
            <h3>필수 역량</h3>
            <ul>
              {result.requirements.map((item, index) => (
                <li key={index}>{item}</li>
              ))}
            </ul>
            
            <h3>우대 사항</h3>
            <ul>
              {result.preferred.map((item, index) => (
                <li key={index}>{item}</li>
              ))}
            </ul>

            <h3>핵심 키워드</h3>
            <ul>
              {result.keywords.map((item, index) => (
                <li key={index}>{item}</li>
              ))}
            </ul>

            <button
              onClick={handleCreateResearchPlan}
              disabled={loading}
            >
              {loading ? "생성 중 ..." : "Research Plan 생성"}
            </button>
          </section>
        )}

        {researchPlan &&(
          <section>
            <h2>Research Plan</h2>

            <p>
              <strong>기업:</strong> {researchPlan.company}
            </p>
            <p>
              <strong>직무:</strong> {researchPlan.position}
            </p>

            {researchPlan.queries.map((item,index)  => (
              <div key={index}>
                <h3>
                  {index + 1}. {item.topic}
                </h3>
                
                <p>
                  <strong>검색어:</strong> {item.query}
                </p>
                <p>
                  <strong>조사 이유:</strong> {item.reason}
                </p>
              </div>
            ))}
          </section>
        )}

    </main>
  );
}

export default App;
