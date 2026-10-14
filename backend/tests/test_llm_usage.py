import asyncio
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.app.llm.usage import record_usage, response_usage
from backend.app.models import JobAnalysis
from backend.tests.test_web_research import post_json


def reply(input_tokens=3000, output_tokens=1000, cached=1000):
    return SimpleNamespace(id="resp_test", usage=SimpleNamespace(input_tokens=input_tokens,
        output_tokens=output_tokens, input_tokens_details=SimpleNamespace(cached_tokens=cached)))


class UsageTests(unittest.TestCase):
    def test_cache_discount_and_cost(self):
        entry = response_usage(reply(), "gpt-4.1-mini", "job_analysis")
        self.assertEqual(entry["estimated_cost_usd"], "0.0025")
        self.assertEqual(entry["total_tokens"], 4000)
        self.assertEqual(entry["cached_input_tokens"], 1000)

    def test_unknown_model_and_missing_usage(self):
        self.assertIsNone(response_usage(reply(), "unregistered", "job_analysis")["estimated_cost_usd"])
        self.assertIsNone(response_usage(SimpleNamespace(), "gpt-4.1-mini", "job_analysis"))
        self.assertIsNone(response_usage(reply(-1), "gpt-4.1-mini", "job_analysis"))

    def test_request_header_has_usage_and_next_request_does_not_leak(self):
        def analyze(text, target):
            record_usage(reply(), "gpt-4.1-mini", "job_analysis")
            return JobAnalysis(company="회사", position="직무", responsibilities=[], requirements=[], preferred=[], keywords=[])
        with patch("backend.app.main.analyze_job", side_effect=analyze):
            status, _, headers = asyncio.run(post_json("/api/jobs/analyze", {"job_text": "공고"}, True))
        self.assertEqual(status, 200)
        entries = json.loads(headers[b"x-llm-usage"])
        self.assertEqual(entries[0]["estimated_cost_usd"], "0.0025")
        with patch("backend.app.main.fetch_job_details", return_value={"job_text":"공고", "roles":[]}):
            _, _, headers = asyncio.run(post_json("/api/jobs/fetch", {"job_url":"https://example.com/"}, True))
        self.assertNotIn(b"x-llm-usage", headers)

    def test_concurrent_requests_keep_separate_usage(self):
        def analyze(text, target):
            record_usage(reply(int(text), 100, 0), "gpt-4.1-mini", "job_analysis")
            return JobAnalysis(company="회사", position="직무", responsibilities=[], requirements=[], preferred=[], keywords=[])
        async def requests():
            return await asyncio.gather(*(post_json("/api/jobs/analyze", {"job_text":str(n)}, True) for n in (200, 900)))
        with patch("backend.app.main.analyze_job", side_effect=analyze):
            results = asyncio.run(requests())
        counts = [json.loads(headers[b"x-llm-usage"])[0]["input_tokens"] for _, _, headers in results]
        self.assertEqual(counts, [200, 900])
