import "./App.css"

import {useState} from "react";
// api.ts에서 만든 analyzeJob 함수를 가져옴
import {analyzeJob, 
        createResearchPlan, 
        runWebResearch,
        createResearchReport,
        fetchJobPosting } from "./api";

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

interface SearchResult{
  title: string;
  url: string;
  snippet: string;
}

interface ResearchResult{
  topic: string;
  query: string;
  reason: string;
  results: SearchResult[];
}

interface WebResearch{
  company: string;
  position: string;
  research_results: ResearchResult[];
}

interface ReportSource{
  title : string;
  url : string;
}

interface ReportSection{
  topic : string;
  query : string;
  summary : string[];
  sources : ReportSource[];
}

interface ResearchReport{
  company : string;
  position : string;
  sections : ReportSection[];
}

// Backend에서 사용하는 Topic 을 사용자 친화적으로 수정
const topicLabels: Record<string, string> = {
  company_business : "기업 주요 사업",
  job_role : "지원 직무",
  technology : "핵심 기술",
  recent_news : "최근 뉴스",
  company_strategy : "기업 전략",
};

// React의 메인 컴포넌트
// 현재 화면에 표시되는 UI를 담당함
function App() {
  const [jobText, setJobText] = useState("");
  const [result, setResult] = useState<JobAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [researchPlan, setResearchPlan] = useState<ResearchPlan | null>(null);
  const [webResearch, setWebResearch] = useState<WebResearch | null>(null);
  const [researchReport, setResearchReport] = useState<ResearchReport | null>(null);
  const [jobUrl, setJobUrl] = useState("");

  const handleFetchJobPosting = async () => {
    // URL이 비어 있으면 실행하지 않음
    if (!jobUrl){
      return;
    }

    try{
      setLoading(true);
      setError("");

      // Backend에 URL 전달
      const data = await fetchJobPosting(jobUrl);

      // 추출된 텍스트를 기존의 text area에 자동 입력
      setJobText(data.job_text);
    } catch {
      setError("채용공고 URL을 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async() => {
    try{
      setLoading(true);
      setError("");
      setResult(null);
      setResearchPlan(null);
      setWebResearch(null);
      setResearchReport(null);

      const data = await analyzeJob(jobText);

      setResult(data);

    } catch{
      setError("채용공고 분석에 실패했습니다. Backend 상태를 확인해주세요");

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

  const handleRunWebResearch = async() => {
    if (!researchPlan) {
      return;
    }

    try{
      setLoading(true);
      setError("");
      setResearchReport(null);

      const data = await runWebResearch(researchPlan);

      setWebResearch(data);
    } catch{
      setError("웹 검색 중 오류가 발생했습니다. 일부 검색어에서 결과가 없을 수 있습니다.");
    }finally{
      setLoading(false);
    }
  };

  const handleCreateResearchReport = async () => {
    if (!webResearch){
      return;
    }

    try{
      setLoading(true);
      setError("");
      
      // Backenddp Web Research 결과 전달
      const report = await createResearchReport(webResearch);
      // 반환된 Report 저장
      setResearchReport(report);
    } catch{
      setError("Research Report 생성에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main>
      <h1>
        Company Research Agent
      </h1>

      {/* API 요청이 진행 중일 때 표시 */}
      {loading && (
        <p>
          요청을 처리하고 있습니다...
        </p>
      )}

      {/* 에러 메세지가 존재할 때 표사 */}
      {error && (
        <p>
          {error}
        </p>
      )}

      <p>
        채용공고를 입력하면 기업과 직무 정보를 분석합니다.
      </p>

      <section>
        <h2>채용공고 입력</h2>

        <p>
          채용공고 URL을 입력하거나 
          직접 내용을 붙여넣을 수 있습니다.
        </p>

        {/* 채용공고 URL 입력 */}
        <input
          type="url"
          value={jobUrl}
          onChange={(event) => setJobUrl(event.target.value)}
          placeholder="https://example.com/job"
        />

        {/* URL에서 채용공고 내용 가져오가 */}
        <button
          onClick={handleFetchJobPosting}
          disabled={!jobUrl || loading}
        >
          {loading ? "불러오는 중..." : "URL에서 채용공고 가져오기"}
        </button>
      </section>

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
                  {index + 1}. {topicLabels[item.topic] ?? item.topic}
                </h3>
                
                <p>
                  <strong>검색어:</strong> {item.query}
                </p>
                <p>
                  <strong>조사 이유:</strong> {item.reason}
                </p>
              </div>
            ))}
            <button
              onClick={handleRunWebResearch}
              disabled={loading}
            >
              {loading ? "검색 중..." : "웹 리서치 시작"}
            </button>
          </section>
        )}

        {webResearch && (
          <section>
            <h2>Web Research</h2>

            {webResearch.research_results.map((research,index) => (
              <div key={index}>

                <h3>
                  {index + 1}. {topicLabels[research.topic] ?? research.topic}
                </h3>

                <p>
                  <strong>검색어:</strong> {research.query}
                </p>
                
                {research.results.length > 0 ? (
                  research.results.map((result, resultIndex) => (
                    <div key={resultIndex}>

                      <h4>{result.title}</h4>
                      <p>{result.snippet}</p>

                      <a
                        href={result.url}
                        target="_blank"
                        rel="noopener"
                      >
                        출처 보기
                      </a>
                    </div>
                    ))) : (
                    <p>
                      해당 검색어에서는 검색 결과를 
                      찾지 못했습니다.
                    </p>
                )}
              </div>
            ))}
            <button
              onClick={handleCreateResearchReport}
              disabled={loading}
            >
              {loading ? "Report 생성 중..." :" Research Report 생성"}
            </button>
          </section>  
        )}

        {researchReport && (
          <section>

            <h2>Research Report</h2>

            <p>
              <strong>기업:</strong> {" "}
              {researchReport.position}
            </p>

            {/* Topic별 Report Section 출력 */}
            {researchReport.sections.map((section, index) => (
              <div key={index}>

                <h3>
                  {index + 1}.{topicLabels[section.topic] ?? section.topic}
                </h3>

                <p>
                  <strong>검색 Query:</strong>{" "}
                  {section.query}
                </p>

                <h4>핵심 내용</h4>

                <ul>
                  {section.summary.map((summary, summaryIndex) => (
                    <li key={summaryIndex}>
                      {summary}
                    </li>
                  ))}
                </ul>

                <h4>출처</h4>

                <ul>
                  {section.sources.map((source, sourceIndex) => (
                    <li key={sourceIndex}>
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        {source.title || "출처 보기"}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </section>
        )}
      
    </main>
  );
}

export default App;
