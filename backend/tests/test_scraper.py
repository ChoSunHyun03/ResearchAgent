import gzip
import socket
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from urllib3.exceptions import HTTPError, ReadTimeoutError

from backend.app.models import PageContent
from backend.app.scraper import PageFetchError, extract_html, fetch_job_posting, fetch_page, validate_target


HTML = (Path(__file__).parent / "fixtures/source_page.html").read_bytes()


def address(ip="93.184.216.34"):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 443))]


def response(status=200, headers=None, chunks=None):
    result = MagicMock(status=status, headers=headers or {"Content-Type": "text/html"})
    result.read.side_effect = chunks if chunks is not None else [HTML, b""]
    return result


class ScraperTests(unittest.TestCase):
    def test_invalid_url_does_not_resolve_dns(self):
        with patch("backend.app.scraper.socket.getaddrinfo") as dns:
            for url in ("file:///etc/passwd", "https://user:pass@example.com/", "https://example.com:9000/", "https://example.com:0/",
                        "https:///missing", "https://example.com/a b", "https://example.com\\evil"):
                with self.subTest(url=url), self.assertRaises(PageFetchError) as caught:
                    validate_target(url)
                self.assertEqual(caught.exception.kind, "unsafe_url")
            dns.assert_not_called()

    def test_nonpublic_and_mixed_dns_are_rejected(self):
        for ips in (["127.0.0.1"], ["10.0.0.1"], ["169.254.169.254"], ["::1"], ["::ffff:127.0.0.1"],
                    ["93.184.216.34", "192.168.1.1"]):
            with self.subTest(ips=ips), patch("backend.app.scraper.socket.getaddrinfo", return_value=[entry for ip in ips for entry in address(ip)]):
                with self.assertRaises(PageFetchError) as caught:
                    validate_target("https://example.com/")
                self.assertEqual(caught.exception.kind, "unsafe_url")

    def test_dns_failure_has_safe_message(self):
        with patch("backend.app.scraper.socket.getaddrinfo", side_effect=OSError("private detail")):
            with self.assertRaises(PageFetchError) as caught:
                validate_target("https://example.com/")
        self.assertEqual(caught.exception.kind, "network")
        self.assertNotIn("private detail", str(caught.exception))

    def test_connection_pins_ip_and_preserves_tls_hostname(self):
        with patch("backend.app.scraper.socket.getaddrinfo", return_value=address()) as dns, patch("backend.app.scraper.urllib3.HTTPSConnectionPool") as pool:
            reply = response()
            pool.return_value.urlopen.return_value = reply
            page = fetch_page("https://example.com/tech?id=7")
        pool.assert_called_once_with("93.184.216.34", port=443, server_hostname="example.com", assert_hostname="example.com", cert_reqs="CERT_REQUIRED")
        self.assertEqual(dns.call_count, 1)
        arguments = pool.return_value.urlopen.call_args
        self.assertEqual(arguments.args, ("GET", "/tech?id=7"))
        self.assertEqual(arguments.kwargs["headers"]["Host"], "example.com")
        self.assertFalse(arguments.kwargs["redirect"])
        self.assertFalse(arguments.kwargs["retries"])
        self.assertEqual(page.status, "success")
        self.assertIn("Python", page.text)
        self.assertIsNotNone(page.fetched_at)
        reply.close.assert_called_once()
        pool.return_value.close.assert_called_once()

    def test_relative_redirect_is_revalidated(self):
        with patch("backend.app.scraper.socket.getaddrinfo", return_value=address()) as dns, patch("backend.app.scraper.urllib3.HTTPSConnectionPool") as pool:
            pool.return_value.urlopen.side_effect = [response(302, {"Location": "/article"}), response()]
            page = fetch_page("https://example.com/start")
        self.assertEqual(dns.call_count, 2)
        self.assertEqual(page.final_url, "https://example.com/article")

    def test_redirect_to_private_address_is_blocked_before_connection(self):
        with patch("backend.app.scraper.socket.getaddrinfo", side_effect=[address(), address("127.0.0.1")]), patch("backend.app.scraper.urllib3.HTTPSConnectionPool") as pool:
            pool.return_value.urlopen.return_value = response(302, {"Location": "http://127.0.0.1/"})
            with self.assertRaises(PageFetchError) as caught:
                fetch_page("https://example.com/")
        self.assertEqual(caught.exception.kind, "unsafe_url")
        pool.assert_called_once()

    def test_redirect_loop_is_bounded(self):
        with patch("backend.app.scraper.socket.getaddrinfo", return_value=address()), patch("backend.app.scraper.urllib3.HTTPSConnectionPool") as pool:
            pool.return_value.urlopen.return_value = response(302, {"Location": "/again"})
            with self.assertRaises(PageFetchError) as caught:
                fetch_page("https://example.com/")
        self.assertEqual(caught.exception.kind, "redirect")
        self.assertEqual(pool.call_count, 4)

    def test_unsupported_content_and_compression_are_rejected(self):
        for headers in ({"Content-Type": "application/pdf"}, {"Content-Type": "text/html", "Content-Encoding": "br"}):
            with self.subTest(headers=headers), patch("backend.app.scraper.socket.getaddrinfo", return_value=address()), patch("backend.app.scraper.urllib3.HTTPSConnectionPool") as pool:
                reply = response(headers=headers)
                pool.return_value.urlopen.return_value = reply
                with self.assertRaises(PageFetchError) as caught:
                    fetch_page("https://example.com/")
                self.assertEqual(caught.exception.kind, "unsupported")
                reply.read.assert_not_called()

    def test_http_failure_is_distinct(self):
        with patch("backend.app.scraper.socket.getaddrinfo", return_value=address()), patch("backend.app.scraper.urllib3.HTTPSConnectionPool") as pool:
            pool.return_value.urlopen.return_value = response(status=403)
            with self.assertRaises(PageFetchError) as caught:
                fetch_page("https://example.com/")
        self.assertEqual(caught.exception.kind, "http")

    def test_byte_limit_rejects_response(self):
        with patch("backend.app.scraper.socket.getaddrinfo", return_value=address()), patch("backend.app.scraper.urllib3.HTTPSConnectionPool") as pool, patch("backend.app.scraper.MAX_PAGE_BYTES", 10):
            pool.return_value.urlopen.return_value = response(chunks=[b"01234567890"])
            with self.assertRaises(PageFetchError) as caught:
                fetch_page("https://example.com/")
        self.assertEqual(caught.exception.kind, "too_large")

    def test_timeout_and_network_errors_are_distinct(self):
        for error, kind in ((ReadTimeoutError(None, "/", "private detail"), "timeout"), (HTTPError("private detail"), "network")):
            with self.subTest(kind=kind), patch("backend.app.scraper.socket.getaddrinfo", return_value=address()), patch("backend.app.scraper.urllib3.HTTPSConnectionPool") as pool:
                pool.return_value.urlopen.side_effect = error
                with self.assertRaises(PageFetchError) as caught:
                    fetch_page("https://example.com/")
                self.assertEqual(caught.exception.kind, kind)
                self.assertNotIn("private detail", str(caught.exception))

    def test_expired_budget_does_not_connect(self):
        with patch("backend.app.scraper.socket.getaddrinfo") as dns:
            with self.assertRaises(PageFetchError) as caught:
                fetch_page("https://example.com/", seconds=0)
            dns.assert_not_called()
        self.assertEqual(caught.exception.kind, "timeout")

    def test_article_extraction_and_truncation(self):
        title, text, truncated = extract_html(HTML, max_chars=12000)
        self.assertEqual(title, "가상회사 기술 소개")
        self.assertIn("Docker", text)
        for excluded in ("로그인", "공통 안내", "숨겨진 내용", "ignore()", "사이트 메뉴"):
            self.assertNotIn(excluded, text)
        self.assertFalse(truncated)
        _, shortened, truncated = extract_html(HTML, max_chars=10)
        self.assertEqual(len(shortened), 10)
        self.assertTrue(truncated)

    def test_empty_page_is_not_success(self):
        with self.assertRaises(PageFetchError) as caught:
            extract_html(b"<html><body><script>ignore()</script></body></html>", 100)
        self.assertEqual(caught.exception.kind, "empty_content")

    def test_job_fetch_keeps_string_return_and_length_limit(self):
        with patch("backend.app.scraper.fetch_page", return_value=PageContent(status="success", text="공고 본문")) as fetch:
            self.assertEqual(fetch_job_posting("https://example.com/job"), "공고 본문")
            fetch.assert_called_once_with("https://example.com/job", max_chars=20000)

    def test_gzip_is_decoded_with_size_limit(self):
        with patch("backend.app.scraper.socket.getaddrinfo", return_value=address()), patch("backend.app.scraper.urllib3.HTTPSConnectionPool") as pool:
            pool.return_value.urlopen.return_value = response(headers={"Content-Type": "text/html", "Content-Encoding": "gzip"}, chunks=[gzip.compress(HTML), b""])
            page = fetch_page("https://example.com/")
        self.assertIn("Docker", page.text)
        with patch("backend.app.scraper.socket.getaddrinfo", return_value=address()), patch("backend.app.scraper.urllib3.HTTPSConnectionPool") as pool, patch("backend.app.scraper.MAX_PAGE_BYTES", 1000):
            pool.return_value.urlopen.return_value = response(headers={"Content-Type": "text/html", "Content-Encoding": "gzip"}, chunks=[gzip.compress(b"x" * 2000), b""])
            with self.assertRaises(PageFetchError) as caught:
                fetch_page("https://example.com/")
        self.assertEqual(caught.exception.kind, "too_large")

    def test_incomplete_gzip_is_rejected(self):
        with patch("backend.app.scraper.socket.getaddrinfo", return_value=address()), patch("backend.app.scraper.urllib3.HTTPSConnectionPool") as pool:
            pool.return_value.urlopen.return_value = response(headers={"Content-Type": "text/html", "Content-Encoding": "gzip"}, chunks=[gzip.compress(HTML)[:-8], b""])
            with self.assertRaises(PageFetchError) as caught:
                fetch_page("https://example.com/")
        self.assertEqual(caught.exception.kind, "network")

    def test_main_with_multiple_articles_keeps_hiring_sections(self):
        html = '<html><head><title>가상회사 신입 채용</title></head><body><main><article>회사 소개</article><article>AI Engineer 주요 업무: 모델 개발</article><section>지원자격: 학사 이상</section></main></body></html>'.encode()
        _, text, _ = extract_html(html, 20000)
        self.assertIn("가상회사 신입 채용", text)
        self.assertIn("AI Engineer", text)
        self.assertIn("지원자격", text)

    def test_multiple_articles_without_main_are_combined(self):
        html = '<html><body><article>AI Engineer 업무: Python</article><article>AX PM 업무: 기획</article></body></html>'.encode()
        _, text, _ = extract_html(html, 20000)
        self.assertIn("AI Engineer", text)
        self.assertIn("AX PM", text)

    def test_title_alone_is_not_valid_body(self):
        with self.assertRaises(PageFetchError):
            extract_html(b'<html><head><title>Job</title></head><body></body></html>', 20000)
