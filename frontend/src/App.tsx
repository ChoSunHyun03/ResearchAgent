import "./App.css"

import {useEffect, useRef, useState} from "react";
// api.ts에서 만든 analyzeJob 함수를 가져옴
import {analyzeJob, 
        createResearchPlan, 
        runWebResearch,
        collectWebSources,
        createResearchReport,
        fetchJobPosting } from "./api";

interface LLMUsage {
  response_id: string | null;
  operation: string;
  model: string;
  input_tokens: number;
  cached_input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  estimated_cost_usd: string | null;
  pricing_date: string | null;
}
interface PostingRole {
  id: string;
  group: string;
  position: string;
  responsibilities: string[];
  requirements: string[];
  competencies: string[];
  preferred: string[];
  analysis_text: string;
  application_url: string;
}
interface JobPosting {
  job_text: string;
  company: string;
  roles: PostingRole[];
  warnings: string[];
  source_url: string;
}

interface JobAnalysis {
  company: string;
  position: string;
  responsibilities: string[];
  requirements: string[];
  preferred: string[];
  keywords: string[];
  competencies?: string[];
  llm_usage?: LLMUsage[];
  analysis_status?: "ready" | "needs_selection" | "missing_details";
  available_positions?: string[];
  analysis_message?: string;
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
  llm_usage?: LLMUsage[];
}

interface PageContent {
  status: "success" | "error" | "skipped";
  final_url: string;
  title: string;
  text: string;
  truncated: boolean;
  fetched_at: string | null;
  error_kind: string | null;
  error_message: string | null;
}

interface SearchResult{
  title: string;
  url: string;
  snippet: string;
  page?: PageContent | null;
}

interface ResearchResult{
  topic: string;
  query: string;
  reason: string;
  results: SearchResult[];
  status?: "success" | "no_results" | "error";
  error_kind?: string | null;
  error_message?: string | null;
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
  status?: "success" | "no_results" | "error";
  error_kind?: string | null;
  error_message?: string | null;
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

// LLM의 자유 주제명은 한국어면 그대로, 내부 영문 코드는 검색어로 설명합니다.
const getTopicLabel = (topic: string, query: string) =>
  topicLabels[topic] || (/[가-힣]/.test(topic) ? topic : query);

// 원문은 요청용으로 보관하고, 사용자가 보는 결과는 분석 상태별로 나눕니다.
function App() {
  const [inputMode, setInputMode] = useState<"url" | "text">("url");
  const [jobUrl, setJobUrl] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [jobText, setJobText] = useState("");
  const [targetPosition, setTargetPosition] = useState("");
  const [posting, setPosting] = useState<JobPosting | null>(null);
  const [selectedGroup, setSelectedGroup] = useState("");
  const [selectedRoleId, setSelectedRoleId] = useState("");
  const [analysisCache, setAnalysisCache] = useState<Record<string, JobAnalysis>>({});
  const [usageRecords, setUsageRecords] = useState<LLMUsage[]>([]);
  const selectedRole = posting?.roles.find(role => role.id === selectedRoleId);
  const groups = [...new Set(posting?.roles.map(role => role.group) ?? [])];
  const [positions, setPositions] = useState<string[]>([]);
  const [result, setResult] = useState<JobAnalysis | null>(null);
  const [researchPlan, setResearchPlan] = useState<ResearchPlan | null>(null);
  const [webResearch, setWebResearch] = useState<WebResearch | null>(null);
  const [researchReport, setResearchReport] = useState<ResearchReport | null>(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [inputNotice, setInputNotice] = useState("");
  const [editing, setEditing] = useState(false);
  const [checked, setChecked] = useState(false);
  const textInput = useRef<HTMLTextAreaElement>(null);
  const resultHeading = useRef<HTMLHeadingElement>(null);
  const rolesHeading = useRef<HTMLHeadingElement>(null);
  const loading = Boolean(busy);
  const ready = Boolean(result && (result.analysis_status ?? "ready") === "ready"
    && result.company && result.position);
  const currentStep = ready ? 3 : result || posting?.roles.length ? 2 : 1;

  // 분석 후 결과 제목에 초점을 옮겨 다음 선택·결과를 쉽게 찾도록 합니다.
  useEffect(() => { if (result) resultHeading.current?.focus(); }, [result]);
  useEffect(() => { if (editing) textInput.current?.focus(); }, [editing]);
  useEffect(() => { if (posting?.roles.length) rolesHeading.current?.focus(); }, [posting]);

  const resetResearch = () => {
    setResearchPlan(null); setWebResearch(null); setResearchReport(null);
  };
  const resetResults = () => {
    setResult(null); setPositions([]); setPosting(null); setSelectedGroup(""); setSelectedRoleId("");
    setAnalysisCache({}); setChecked(false); resetResearch(); setError("");
  };
  const switchInput = (mode: "url" | "text") => {
    if (inputMode === mode) return;
    setInputMode(mode); setJobText(""); setSourceUrl(""); setTargetPosition("");
    setInputNotice(""); setEditing(false); resetResults();
  };

  // 처음에는 직무 후보를 확인하고, 선택 후 같은 원문을 해당 직무로 재분석합니다.
  const receiveAnalysis = async (text: string, position: string, cacheKey = "") => {
    const data: JobAnalysis = await analyzeJob(text, position);
    setResult(data);
    setUsageRecords(previous => [...previous, ...(data.llm_usage ?? [])]);
    if (cacheKey && data.analysis_status === "ready") {
      setAnalysisCache(previous => ({...previous, [cacheKey]: data}));
    }
    if (data.available_positions?.length) setPositions(data.available_positions);
    setEditing(false);
  };
  const handleFetch = async () => {
    if (!jobUrl.trim() || loading) return;
    resetResults(); setJobText(""); setSourceUrl(""); setTargetPosition(""); setInputNotice("");
    setBusy("공고 내용을 가져오고 있습니다…");
    try {
      const data: JobPosting = await fetchJobPosting(jobUrl.trim());
      setJobText(data.job_text); setSourceUrl(data.source_url || jobUrl.trim()); setChecked(true);
      setInputNotice((data.warnings ?? []).join(" "));
      setPosting(data);
      if (data.roles?.length) {
        // 실제 수집 목록으로 선택 버튼을 만듭니다. 이 단계는 LLM 호출이 없습니다.
        setSelectedGroup(data.roles[0].group);
        setEditing(false);
      } else {
        setBusy("모집 직무와 지원 조건을 확인하고 있습니다…");
        await receiveAnalysis(data.job_text, "");
      }
    } catch (e) {
      setError(e instanceof Error && !(e instanceof TypeError) ? e.message : "공고를 확인하지 못했습니다. 상세 공고 내용을 직접 붙여넣어 주세요.");
    } finally { setBusy(""); }
  };
  const handleAnalyze = async (position = targetPosition, text = jobText, cacheKey = "") => {
    if (!text.trim() || loading) return;
    setSelectedRoleId(cacheKey);
    if (cacheKey && analysisCache[cacheKey]) {
      setResult(analysisCache[cacheKey]); setTargetPosition(position); setError(""); resetResearch(); return;
    }
    setTargetPosition(position); setChecked(true); setError(""); setResult(null); resetResearch();
    setBusy(position ? `${position}의 지원 조건을 확인하고 있습니다…` : "모집 직무와 지원 조건을 확인하고 있습니다…");
    try { await receiveAnalysis(text, position, cacheKey); }
    catch (e) { setError(e instanceof Error && !(e instanceof TypeError) ? e.message : "공고 분석에 실패했습니다."); }
    finally { setBusy(""); }
  };
  const handlePlan = async () => {
    if (!ready || !result || loading) return;
    setBusy("이 직무에 맞는 조사 항목을 준비하고 있습니다…"); setError(""); resetResearch();
    try {
      const plan: ResearchPlan = await createResearchPlan(result);
      setResearchPlan(plan);
      setUsageRecords(previous => [...previous, ...(plan.llm_usage ?? [])]);
    }
    catch { setError("조사 항목을 준비하지 못했습니다. 다시 시도해 주세요."); }
    finally { setBusy(""); }
  };
  const handleSearch = async () => {
    if (!researchPlan || loading) return;
    setBusy("기업과 직무에 관한 자료를 검색하고 있습니다…"); setError("");
    setWebResearch(null); setResearchReport(null);
    try { setWebResearch(await runWebResearch(researchPlan)); }
    catch { setError("자료 검색에 실패했습니다. 잠시 후 다시 시도해 주세요."); }
    finally { setBusy(""); }
  };
  const handleCollect = async () => {
    if (!webResearch || loading) return;
    setBusy("검색한 자료의 본문을 가져오고 있습니다…"); setError(""); setResearchReport(null);
    try { setWebResearch(await collectWebSources(webResearch)); }
    catch { setError("일부 본문을 가져오지 못했습니다. 검색 결과로 보고서를 만들 수 있습니다."); }
    finally { setBusy(""); }
  };
  const handleReport = async () => {
    if (!webResearch || loading) return;
    setBusy("검색 결과를 보고서로 정리하고 있습니다…"); setError("");
    try { setResearchReport(await createResearchReport(webResearch)); }
    catch { setError("보고서 생성에 실패했습니다. 다시 시도해 주세요."); }
    finally { setBusy(""); }
  };

  const textEditor = <>
    <label htmlFor="job-text">채용공고 내용</label>
    <textarea id="job-text" ref={textInput} value={jobText} disabled={loading} maxLength={20000}
      placeholder="회사명, 모집 직무, 주요 업무, 지원자격이 포함된 상세 공고를 붙여넣어 주세요."
      onChange={e => { setJobText(e.target.value); setSourceUrl(""); resetResults(); setInputNotice(""); }} />
    <p className="hint">{jobText.length.toLocaleString()} / 20,000자 · 여러 직무가 있으면 확인 후 선택합니다.</p>
    <button disabled={loading || !jobText.trim()} onClick={() => handleAnalyze()}>입력한 내용으로 공고 확인</button>
  </>;
  const roleEditor = <form className="role-form" onSubmit={e => { e.preventDefault(); void handleAnalyze(); }}>
    <label htmlFor="target-position">지원 직무 직접 입력</label>
    <div className="input-row">
      <input id="target-position" value={targetPosition} maxLength={120} disabled={loading}
        placeholder="공고에 적힌 직무명을 입력하세요" onChange={e => setTargetPosition(e.target.value)} />
      <button disabled={loading || !targetPosition.trim() || !jobText.trim()}>이 직무로 확인</button>
    </div>
    <p className="hint">입력한 직무의 상세 내용이 원문에 있어야 분석할 수 있습니다.</p>
  </form>;

  return <main>
    <header className="app-header">
      <p className="eyebrow">COMPANY RESEARCH AGENT</p>
      <h1>지원할 직무부터, 필요한 기업 정보까지</h1>
      <p className="subtitle">채용공고를 확인하고 내 직무의 업무와 지원 조건을 한눈에 살펴보세요.</p>
    </header>
    <ol className="steps" aria-label="진행 순서">
      {["공고 입력", "직무 확인", "핵심 정보 · 기업 조사"].map((label, i) =>
        <li key={label} className={currentStep === i + 1 ? "active" : currentStep > i + 1 ? "done" : ""}
          aria-current={currentStep === i + 1 ? "step" : undefined}><span>{i + 1}</span>{label}</li>)}
    </ol>
    <div aria-live="polite" role="status">{busy && <p className="notice processing">{busy}</p>}</div>
    {error && <p role="alert" className="notice error">{error}</p>}

    <section className="panel" aria-labelledby="input-heading" aria-busy={loading}>
      <div className="section-heading"><div><p className="eyebrow">01 / 채용공고</p><h2 id="input-heading">어떤 공고에 지원하시나요?</h2></div>
        {sourceUrl && <a href={sourceUrl} target="_blank" rel="noopener noreferrer">공고 사이트 보기 ↗</a>}</div>
      <div className="input-tabs" role="group" aria-label="공고 입력 방식">
        <button className="tab" aria-pressed={inputMode === "url"} disabled={loading} onClick={() => switchInput("url")}>URL로 가져오기</button>
        <button className="tab" aria-pressed={inputMode === "text"} disabled={loading} onClick={() => switchInput("text")}>내용 직접 붙여넣기</button>
      </div>
      {inputMode === "url" && <form onSubmit={e => { e.preventDefault(); void handleFetch(); }}>
        <label htmlFor="job-url">채용공고 URL</label>
        <div className="input-row"><input id="job-url" type="url" value={jobUrl} disabled={loading}
          placeholder="https://기업의-채용공고-주소" required onChange={e => {
            setJobUrl(e.target.value); setJobText(""); setSourceUrl(""); setTargetPosition("");
            setInputNotice(""); resetResults();
          }} /><button disabled={loading || !jobUrl.trim()}>공고 확인하기</button></div>
        <p className="hint">내용을 가져온 뒤 모집 직무를 확인합니다. 원문 전체는 아래에서 필요할 때 펼쳐볼 수 있습니다.</p>
      </form>}
      {inputMode === "text" && !checked ? textEditor : jobText &&
        <details className="raw-editor" open={editing} onToggle={e => setEditing(e.currentTarget.open)}>
          <summary>가져온 원문 확인 · 수정</summary><p className="hint">전체 수집 내용입니다. 분석 결과는 아래의 직무별 핵심 정보에서 확인하세요.</p>{textEditor}
        </details>}
      {inputNotice && <p className="hint">{inputNotice}</p>}
    </section>

    {posting && posting.roles.length > 0 && <section className="panel" aria-labelledby="roles-heading">
      <p className="eyebrow">02 / 지원 직무 선택</p>
      <h2 id="roles-heading" tabIndex={-1} ref={rolesHeading}>{posting.company}의 모집 직무</h2>
      <p className="subtitle">직군을 고른 뒤 지원할 세부 직무를 선택하세요. 선택한 직무의 조건만 확인합니다.</p>
      <div className="group-options" role="group" aria-label="모집 직군">
        {groups.map(group => <button key={group} className="secondary" aria-pressed={selectedGroup === group}
          disabled={loading} onClick={() => {
            if (group !== selectedGroup) {
              setSelectedGroup(group); setSelectedRoleId(""); setTargetPosition(""); setResult(null); setError(""); resetResearch();
            }
          }}>{group}</button>)}
      </div>
      <div className="role-options" role="group" aria-label="세부 직무">
        {posting.roles.filter(role => role.group === selectedGroup).map(role =>
          <button key={role.id} className="role-option" aria-pressed={role.id === selectedRoleId} disabled={loading}
            onClick={() => handleAnalyze(role.position, role.analysis_text, role.id)}>
            {role.position}<span>{role.id === selectedRoleId ? "선택한 직무" : "이 직무의 공고 확인 →"}</span>
          </button>)}
      </div>
      <p className="hint">공고에서 수집한 직무 {posting.roles.length}개 · 직무 분석 결과는 이 화면에서 재사용합니다.</p>
      {selectedRole && <details open={!result} className="selected-posting">
        <summary>{selectedRole.position} 직무 상세 공고</summary>
        <div className="facts-grid">
          {[{title:"직무기술",items:selectedRole.responsibilities}, {title:"자격요건",items:selectedRole.requirements},
            {title:"필수 · 필요 역량",items:selectedRole.competencies}, {title:"우대 역량 · 우대사항",items:selectedRole.preferred}].map(group =>
            <article className="fact-card" key={group.title}><h3>{group.title}</h3>
              {group.items.length ? <ul>{group.items.map((item,i) => <li key={i}>{item}</li>)}</ul> : <p className="hint">공고에서 확인되지 않았습니다.</p>}
            </article>)}
        </div>
        <a className="application-link" href={selectedRole.application_url} target="_blank" rel="noopener noreferrer">공식 지원 공고 보기 ↗</a>
      </details>}
      {selectedRole && !result && !loading && <button disabled={loading} onClick={() => handleAnalyze(selectedRole.position, selectedRole.analysis_text, selectedRole.id)}>선택 직무 분석 다시 시도</button>}

    </section>}

    {result && <section className="panel" aria-labelledby="analysis-heading">
      <p className="eyebrow">02 / 지원 직무</p>
      <h2 id="analysis-heading" tabIndex={-1} ref={resultHeading}>
        {ready ? `${result.company} · ${result.position}` : result.analysis_status === "needs_selection" ? "지원할 직무를 선택하세요" : "직무 상세 공고가 필요합니다"}
      </h2>
      {!ready && <>
        {result.company && <p className="company-name">{result.company}</p>}
        <p className="subtitle">{result.analysis_status === "needs_selection"
          ? "여러 모집 직무가 있습니다. 하나를 선택하면 그 직무의 업무와 지원 조건만 정리합니다."
          : "현재 가져온 내용만으로는 직무별 업무와 지원자격을 확인하기 어렵습니다. 원하는 직무의 상세 페이지 URL이나 내용을 추가해 주세요."}</p>
        {!posting?.roles.length && positions.length > 0 && <div className="role-options">{positions.map(position =>
          <button className="role-option" key={position} disabled={loading} onClick={() => handleAnalyze(position)}>{position}<span>이 직무 확인 →</span></button>)}</div>}
        {result.analysis_status === "missing_details" && <button className="secondary" disabled={loading} onClick={() => {
          setInputMode("text"); setChecked(false); setEditing(true);
        }}>직무 상세 내용 붙여넣기</button>}
        <details><summary>지원 직무를 직접 지정하고 싶어요</summary>{roleEditor}</details>
      </>}
      {ready && <>
        <p className="subtitle">선택한 직무의 조건과 공고에 명시된 공통 지원자격을 정리했습니다.</p>
        <div className="facts-grid">
          {[{title:"주요 업무", items:result.responsibilities}, {title:"지원자격", items:result.requirements},
            {title:"필수 · 필요 역량", items:result.competencies ?? []},
            {title:"우대 역량 · 우대사항", items:result.preferred}].map(group => <article className="fact-card" key={group.title}>
              <h3>{group.title}</h3>{group.items.length ? <ul>{group.items.map((item, i) => <li key={i}>{item}</li>)}</ul>
                : <p className="hint">공고에서 확인되지 않았습니다.</p>}
            </article>)}
        </div>
        {result.keywords.length > 0 && <div className="keywords" aria-label="직무 키워드">{result.keywords.map((word,i) => <span key={i}>{word}</span>)}</div>}
        <p className="hint">자동 분석 결과이므로 실제 지원 전 원문과 대조해 주세요.</p>
        {!posting?.roles.length && <details><summary>다른 직무로 확인하기</summary>
          {!posting?.roles.length && positions.length > 0 && <div className="role-options">{positions.map(position => <button key={position} className="secondary"
            disabled={loading || position === result.position} onClick={() => handleAnalyze(position)}>{position}</button>)}</div>}{roleEditor}
        </details>}
      </>}
    </section>}

    {ready && <section className="panel" aria-labelledby="research-heading">
      <p className="eyebrow">03 / 기업 조사</p><h2 id="research-heading">이 직무에 맞는 기업 정보를 찾아보세요</h2>
      {!researchPlan && <><p className="subtitle">사업, 기술, 최근 소식 등 지원 준비에 필요한 조사 항목을 만듭니다.</p>
        <button disabled={loading} onClick={handlePlan}>기업 조사 항목 만들기</button></>}
      {researchPlan && <>
        <div className="topic-list">{researchPlan.queries.map((query,i) => <span key={i}>{getTopicLabel(query.topic, query.query)}</span>)}</div>
        <details><summary>조사 항목과 검색어 보기 ({researchPlan.queries.length}개)</summary>
          {researchPlan.queries.map((query,i) => <article className="research-item" key={i}>
            <h3>{getTopicLabel(query.topic, query.query)}</h3><p>{query.reason}</p><p className="hint">검색어: {query.query}</p>
          </article>)}
        </details>
        {!webResearch && <button disabled={loading} onClick={handleSearch}>이 항목으로 자료 검색하기</button>}
      </>}
      {webResearch && <>
        <p className="research-count">{webResearch.research_results.length}개 조사 항목에서 자료 {webResearch.research_results.reduce((sum,item) => sum + item.results.length,0)}개를 찾았습니다.</p>
        <details><summary>검색한 자료 확인</summary>{webResearch.research_results.map((item,i) =>
          <article className="research-item" key={i}><h3>{getTopicLabel(item.topic, item.query)}</h3>
            {!item.results.length && <p className="hint">{item.status === "error" ? "검색에 실패했습니다. 다시 검색해 주세요." : "검색 결과가 없습니다."}</p>}
            {item.results.map((source,j) => <div className="source-item" key={j}>
              <a href={source.url} target="_blank" rel="noopener noreferrer">{source.title || source.url} ↗</a><p>{source.snippet}</p>
              {source.page && <p className="hint">{source.page.status === "success" ? "본문을 가져왔습니다." : "본문을 가져오지 못해 검색 요약을 유지합니다."}</p>}
              {source.page?.status === "success" && <details><summary>자료 원문 보기</summary><p className="source-text">{source.page.text}</p></details>}
            </div>)}
          </article>)}</details>
        <div className="actions"><button disabled={loading} onClick={handleReport}>{researchReport ? "보고서 다시 정리하기" : "검색 결과로 보고서 만들기"}</button>
          <button className="secondary" disabled={loading} onClick={handleCollect}>자료 본문 가져오기 (선택)</button></div>
        <p className="hint">보고서는 검색 결과의 요약과 출처를 바탕으로 정리됩니다.</p>
        <details><summary>조사를 다시 진행하기</summary><div className="actions"><button className="secondary" disabled={loading} onClick={handleSearch}>자료 다시 검색</button>
          <button className="secondary" disabled={loading} onClick={handlePlan}>조사 항목 다시 만들기</button></div></details>
      </>}
    </section>}

    {researchReport && ready && <section className="panel report" aria-labelledby="report-heading">
      <p className="eyebrow">조사 결과</p><h2 id="report-heading">{researchReport.company} 기업 조사 보고서</h2><p className="subtitle">{researchReport.position} 지원 준비</p>
      {researchReport.sections.map((item,i) => <article className="report-section" key={i}><h3>{getTopicLabel(item.topic, item.query)}</h3>
        {item.status === "error" ? <p className="hint">이 항목은 검색에 실패했습니다. 자료를 다시 검색해 주세요.</p>
          : item.summary.length ? <ul>{item.summary.map((line,j) => <li key={j}>{line}</li>)}</ul> : <p className="hint">확인할 자료가 없습니다.</p>}
        {item.sources.length > 0 && <div className="report-sources"><p className="hint">출처</p>{item.sources.map((source,j) =>
          <a key={j} href={source.url} target="_blank" rel="noopener noreferrer">{source.title || source.url} ↗</a>)}</div>}
      </article>)}
    </section>}
    {usageRecords.length > 0 && <details className="usage-panel"><summary>이번 화면의 API 사용량 · 비용 확인</summary>
      <p className="hint">실제 응답 토큰 기준 계산값입니다. USD, 세금·환율·별도 재시도 비용 제외. 새로고침하면 화면 집계가 초기화됩니다.</p>
      <ul>{usageRecords.map((usage,i) => <li key={i}>
        {usage.operation === "job_analysis" ? "직무 분석" : "조사 항목 생성"}: 입력 {usage.input_tokens.toLocaleString()} / 출력 {usage.output_tokens.toLocaleString()} 토큰
        {usage.cached_input_tokens > 0 && ` (캐시 입력 ${usage.cached_input_tokens.toLocaleString()})`}
        {usage.estimated_cost_usd !== null ? ` · $${Number(usage.estimated_cost_usd).toFixed(8)}` : " · 해당 모델의 요금 정보 없음"}
      </li>)}</ul>
      <p className="hint">계산 가능한 호출 합계: ${usageRecords.reduce((sum,item) => sum + Number(item.estimated_cost_usd ?? 0), 0).toFixed(8)}
        {usageRecords.some(item => item.estimated_cost_usd === null) && " (요금 미등록 호출 제외)"}</p>
    </details>}
    <footer>공고에 없는 조건은 추정하지 않습니다. 지원 직무를 확인한 뒤 기업 조사를 진행하세요.</footer>
  </main>;
}

export default App;
