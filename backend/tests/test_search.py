import json
import unittest
from pathlib import Path
from unittest.mock import patch

from ddgs.exceptions import DDGSException, RatelimitException, TimeoutException

from backend.app.search import SearchError, clean_search_results, normalize_url, search_web


class SearchTests(unittest.TestCase):
    def test_cleanup_examples(self):
        cases = json.loads((Path(__file__).parent / "fixtures/search_cases.json").read_text())
        for case in cases:
            with self.subTest(case=case["id"]):
                actual = [item.model_dump(exclude_none=True) for item in clean_search_results(case["raw"])]
                self.assertEqual(actual, case["expected"])

    def test_url_identity_and_invalid_urls(self):
        # 경로의 대소문자, 검색 파라미터와 기본값이 아닌 포트를 보존합니다.
        self.assertEqual(normalize_url("https://EXAMPLE.com:8443/Jobs?id=2&lang=ko#part"),
                         "https://example.com:8443/Jobs?id=2&lang=ko")
        self.assertEqual(normalize_url("https://example.com/?q=a%20b&sig=A%2fB&utm_source=x"),
                         "https://example.com/?q=a%20b&sig=A%2fB")
        self.assertNotEqual(normalize_url("https://example.com/A"), normalize_url("https://example.com/a"))
        self.assertNotEqual(normalize_url("https://example.com/a"), normalize_url("https://example.com/a/"))
        for value in (None, "", "ftp://example.com/a", "https://user:pass@example.com/",
                      "https://example.com:bad/", "https://example.com/a b", "https:///missing"):
            with self.subTest(value=value):
                self.assertIsNone(normalize_url(value))

    def test_search_requests_bounded_candidates_and_cleans_results(self):
        with patch("backend.app.search.DDGS") as provider:
            provider.return_value.text.return_value = [
                {"title": "첫 결과", "href": "https://example.com/1", "body": " 설명 "},
                {"title": "중복", "href": "https://example.com/1#part", "body": "중복"},
                {"title": "다음", "href": "https://example.com/2", "body": ""},
            ]
            result = search_web("  회사   사업 ", max_results=2)
            self.assertEqual(len(result), 2)
            provider.assert_called_once_with(timeout=10)
            provider.return_value.text.assert_called_once_with(
                "회사 사업", region="kr-kr", safesearch="moderate", max_results=4)

    def test_invalid_input_does_not_contact_search(self):
        with patch("backend.app.search.DDGS") as provider:
            for query, count in ((" ", 3), ("회사", 0)):
                with self.subTest(query=query, count=count):
                    with self.assertRaises(ValueError):
                        search_web(query, count)
            provider.assert_not_called()

    def test_external_failures_are_distinct_and_safe(self):
        for exception, kind in ((TimeoutException, "timeout"),
                                (RatelimitException, "rate_limit"),
                                (DDGSException, "upstream")):
            with self.subTest(kind=kind), patch("backend.app.search.DDGS") as provider:
                provider.return_value.text.side_effect = exception("private upstream detail")
                with self.assertRaises(SearchError) as caught:
                    search_web("회사 사업")
                self.assertEqual(caught.exception.kind, kind)
                self.assertNotIn("private upstream detail", str(caught.exception))

    def test_malformed_response_is_not_no_results(self):
        with patch("backend.app.search.DDGS") as provider:
            for response in (None, {"unexpected": "value"}, "not a list"):
                with self.subTest(response=response):
                    provider.return_value.text.return_value = response
                    with self.assertRaises(SearchError) as caught:
                        search_web("회사 사업")
                    self.assertEqual(caught.exception.kind, "invalid_response")

    def test_completed_empty_search_returns_empty_list(self):
        with patch("backend.app.search.DDGS") as provider:
            provider.return_value.text.return_value = []
            self.assertEqual(search_web("회사 사업"), [])
