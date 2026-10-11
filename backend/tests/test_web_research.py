import asyncio
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from ddgs.exceptions import TimeoutException

from backend.app.main import app
from backend.app.models import JobAnalysis, ResearchPlan, ResearchQuery, WebResearch
from backend.app.research import create_research_report, run_web_research
from backend.app.search import SearchError


def example_plan():
    return ResearchPlan(company="테스트회사", position="AI Engineer", queries=[
        ResearchQuery(topic=topic, query=f"테스트회사 {topic}", reason="직무 조사")
        for topic in ("사업", "기술", "뉴스")
    ])


async def post_json(path, data):
    # 추가 HTTP 패키지 없이 실제 FastAPI ASGI 요청·응답 경계를 검증합니다.
    body = json.dumps(data).encode()
    messages = []
    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}
    async def send(message):
        messages.append(message)
    scope = {"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
             "method": "POST", "scheme": "http", "path": path, "raw_path": path.encode(),
             "query_string": b"", "root_path": "", "headers": [(b"content-type", b"application/json")],
             "client": ("127.0.0.1", 1234), "server": ("test", 80)}
    await app(scope, receive, send)
    status = next(item["status"] for item in messages if item["type"] == "http.response.start")
    payload = b"".join(item.get("body", b"") for item in messages if item["type"] == "http.response.body")
    return status, json.loads(payload)


class WebResearchTests(unittest.TestCase):
    def test_mixed_outcomes_continue_and_report_preserves_failure(self):
        with patch("backend.app.research.search_web", side_effect=[
            [], SearchError("timeout", "검색 시간 초과"), ValueError("empty query")
        ]) as search:
            web = run_web_research(example_plan())
        self.assertEqual(search.call_count, 3)
        self.assertEqual([item.status for item in web.research_results], ["no_results", "error", "error"])
        self.assertEqual(web.research_results[2].error_kind, "invalid_query")
        report = create_research_report(web)
        self.assertEqual(report.sections[1].status, "error")
        self.assertEqual(report.sections[1].error_kind, "timeout")
        self.assertEqual(report.sections[1].error_message, "검색 시간 초과")

    def test_same_source_is_kept_for_distinct_topics(self):
        with patch("backend.app.search.DDGS") as provider:
            provider.return_value.text.return_value = [
                {"title": "공통 출처", "href": "https://example.com/about", "body": "설명"}]
            web = run_web_research(example_plan())
        self.assertEqual([len(item.results) for item in web.research_results], [1, 1, 1])

    def test_legacy_payload_without_status_still_generates_report(self):
        web = WebResearch.model_validate({"company": "회사", "position": "직무", "research_results": [
            {"topic": "사업", "query": "회사 사업", "reason": "조사", "results": [
                {"title": "출처", "url": "https://example.com/", "snippet": "사업 설명"}]}]})
        report = create_research_report(web)
        self.assertEqual(report.sections[0].summary, ["사업 설명"])
        self.assertEqual(report.sections[0].sources[0].url, "https://example.com/")

    def test_search_and_report_http_flow(self):
        with patch("backend.app.search.DDGS") as provider:
            provider.return_value.text.side_effect = [
                [{"title": " 사업 ", "href": "https://EXAMPLE.com/business?utm_source=test", "body": "사업 설명"},
                 {"title": "중복", "href": "https://example.com/business#part", "body": "중복"}],
                [], TimeoutException("private detail")]
            status, web = asyncio.run(post_json("/api/research/search", example_plan().model_dump()))
        self.assertEqual(status, 200)
        self.assertEqual([item["status"] for item in web["research_results"]], ["success", "no_results", "error"])
        self.assertEqual(len(web["research_results"][0]["results"]), 1)
        status, report = asyncio.run(post_json("/api/research/report", web))
        self.assertEqual(status, 200)
        self.assertEqual(report["sections"][0]["summary"], ["사업 설명"])
        self.assertEqual(report["sections"][0]["sources"][0]["url"], "https://example.com/business")
        self.assertEqual(report["sections"][2]["error_kind"], "timeout")
        self.assertNotIn("private detail", json.dumps(report))

    def test_invalid_http_plan_is_rejected_before_search(self):
        with patch("backend.app.research.search_web") as search:
            status, _ = asyncio.run(post_json("/api/research/search", {"company": "회사"}))
        self.assertEqual(status, 422)
        search.assert_not_called()

    def test_evaluation_examples_are_valid_and_cover_missing_fields(self):
        root = Path(__file__).resolve().parents[2]
        cases = json.loads((root / "evaluation/job_analysis_cases.json").read_text())
        self.assertEqual(len({case["id"] for case in cases}), len(cases))
        for case in cases:
            with self.subTest(case=case["id"]):
                self.assertTrue(case["job_text"].strip())
                JobAnalysis.model_validate(case["expected"])
        self.assertTrue(any(not case["expected"]["company"] for case in cases))
        self.assertTrue(any(not case["expected"]["requirements"] for case in cases))
