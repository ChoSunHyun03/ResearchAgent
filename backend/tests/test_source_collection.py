import asyncio
import unittest
from unittest.mock import patch

from backend.app.models import PageContent, WebResearch
from backend.app.research import collect_web_sources, create_research_report
from backend.app.scraper import PageFetchError
from backend.tests.test_web_research import post_json


def example_web(count=2, repeated=False):
    return WebResearch.model_validate({"company": "테스트회사", "position": "AI Engineer", "research_results": [
        {"topic": f"주제 {i}", "query": f"검색 {i}", "reason": "조사", "results": [
            {"title": "출처", "url": f"https://example.com/{0 if repeated else i}", "snippet": "검색 요약"}]}
        for i in range(count)]})


class SourceCollectionTests(unittest.TestCase):
    def test_same_url_is_fetched_once_per_request_without_mutating_input(self):
        original = example_web(repeated=True)
        with patch("backend.app.research.fetch_page", return_value=PageContent(status="success", text="수집 본문")) as fetch:
            collected = collect_web_sources(original)
        fetch.assert_called_once()
        self.assertIsNone(original.research_results[0].results[0].page)
        self.assertEqual([item.results[0].page.text for item in collected.research_results], ["수집 본문", "수집 본문"])

    def test_page_failure_keeps_snippet_and_continues(self):
        with patch("backend.app.research.fetch_page", side_effect=[PageFetchError("http", "접근 실패"), PageContent(status="success", text="다음 본문")]):
            collected = collect_web_sources(example_web())
        self.assertEqual(collected.research_results[0].status, "success")
        self.assertEqual(collected.research_results[0].results[0].page.status, "error")
        self.assertEqual(collected.research_results[1].results[0].page.status, "success")
        report = create_research_report(collected)
        self.assertEqual(report.sections[0].summary, ["검색 요약"])

    def test_unique_page_limit_skips_remaining_sources(self):
        with patch("backend.app.research.fetch_page", return_value=PageContent(status="success", text="본문")) as fetch:
            collected = collect_web_sources(example_web(count=12))
        self.assertEqual(fetch.call_count, 10)
        self.assertEqual(collected.research_results[10].results[0].page.status, "skipped")
        self.assertEqual(collected.research_results[11].results[0].page.error_kind, "budget")

    def test_collection_time_budget_skips_network_calls(self):
        with patch("backend.app.research.time.monotonic", side_effect=[0, 46, 47]), patch("backend.app.research.fetch_page") as fetch:
            collected = collect_web_sources(example_web())
        fetch.assert_not_called()
        self.assertEqual(collected.research_results[0].results[0].page.status, "skipped")

    def test_http_collection_returns_body_and_failure_metadata(self):
        with patch("backend.app.research.fetch_page", side_effect=[PageContent(status="success", title="본문 제목", text="본문", final_url="https://example.com/final"), PageFetchError("timeout", "시간 초과")]):
            status, collected = asyncio.run(post_json("/api/research/collect", example_web().model_dump(mode="json")))
        self.assertEqual(status, 200)
        self.assertEqual(collected["research_results"][0]["results"][0]["page"]["text"], "본문")
        self.assertEqual(collected["research_results"][1]["results"][0]["page"]["error_kind"], "timeout")
        status, report = asyncio.run(post_json("/api/research/report", collected))
        self.assertEqual(status, 200)
        self.assertEqual(report["sections"][0]["summary"], ["검색 요약"])

    def test_legacy_search_result_without_page_is_supported(self):
        web = example_web()
        self.assertIsNone(web.research_results[0].results[0].page)
        self.assertEqual(create_research_report(web).sections[0].summary, ["검색 요약"])

    def test_job_url_endpoint_retains_response_and_safe_errors(self):
        with patch("backend.app.main.fetch_job_posting", return_value="공고 본문"):
            status, payload = asyncio.run(post_json("/api/jobs/fetch", {"job_url": "https://example.com/job"}))
        self.assertEqual(status, 200)
        self.assertEqual(payload["job_text"], "공고 본문")
        self.assertTrue(payload["warnings"])
        with patch("backend.app.main.fetch_job_posting", side_effect=PageFetchError("unsafe_url", "내부 주소 차단")):
            status, payload = asyncio.run(post_json("/api/jobs/fetch", {"job_url": "http://127.0.0.1/"}))
        self.assertEqual(status, 400)
        self.assertEqual(payload["detail"], "내부 주소 차단")
