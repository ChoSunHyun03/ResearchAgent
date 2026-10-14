import ipaddress
import socket
import time
import zlib
from datetime import datetime, timezone
from urllib.parse import quote, urljoin, urlsplit

import urllib3
from bs4 import BeautifulSoup
from urllib3.exceptions import HTTPError, TimeoutError

from backend.app.models import PageContent

MAX_PAGE_BYTES = 1_000_000
MAX_BODY_CHARS = 12000
MAX_REDIRECTS = 3
PAGE_SECONDS = 8


class PageFetchError(ValueError):
    """URL 수집 실패를 안전한 종류와 메시지로 반환합니다."""

    def __init__(self, kind: str, message: str) -> None:
        super().__init__(message)
        self.kind = kind


def validate_target(url: str):
    """연결 전 공개 IP를 확인하고 실제 연결을 해당 IP로 고정합니다."""
    try:
        parts = urlsplit(url)
        if (parts.scheme not in {"http", "https"} or not parts.hostname
                or parts.username is not None or parts.password is not None
                or "\\" in url or any(char.isspace() or ord(char) < 32 for char in url)):
            raise ValueError()
        host = parts.hostname.encode("idna").decode("ascii")
        port = parts.port if parts.port is not None else (443 if parts.scheme == "https" else 80)
        if port not in {80, 443}:
            raise ValueError()
    except (ValueError, UnicodeError):
        raise PageFetchError("unsafe_url", "공개 HTTP(S) 페이지 주소를 확인해주세요.") from None
    try:
        addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except OSError:
        raise PageFetchError("network", "페이지 주소를 찾을 수 없습니다.") from None
    ips = [entry[4][0] for entry in addresses]
    if not ips or any(not ipaddress.ip_address(ip).is_global for ip in ips):
        raise PageFetchError("unsafe_url", "내부 주소나 공개되지 않은 주소는 수집할 수 없습니다.")
    return parts, host, port, ips[0]


def extract_html(html: bytes, max_chars: int) -> tuple[str, str, bool]:
    """본문 영역을 우선하고 실행 코드와 공통 탐색 영역을 제거합니다."""
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    for tag in soup(["script", "style", "noscript", "nav", "header", "footer", "aside", "form"]):
        tag.decompose()
    for tag in soup.select('[hidden], [aria-hidden="true"]'):
        if tag.parent is not None:
            tag.decompose()
    # 여러 article이 있는 채용 안내 페이지는 main 전체를 사용합니다.
    main = soup.find("main")
    articles = [tag for tag in soup.find_all("article") if tag.find_parent("article") is None]
    if main is not None:
        raw_text = main.get_text("\n", strip=True)
    elif articles:
        raw_text = "\n".join(tag.get_text("\n", strip=True) for tag in articles)
    else:
        raw_text = (soup.body or soup).get_text("\n", strip=True)
    lines = [" ".join(line.split()) for line in raw_text.splitlines()]
    text = "\n".join(line for line in lines if line)
    if not text:
        raise PageFetchError("empty_content", "페이지에서 읽을 수 있는 본문을 찾지 못했습니다.")
    # head의 채용 제목에도 회사·채용 유형 정보가 있으므로 원문에 포함합니다.
    if title and title not in text:
        text = title + "\n" + text
    return title, text[:max_chars], len(text) > max_chars


def fetch_document(url: str, seconds: float = PAGE_SECONDS,
                   content_types: frozenset[str] = frozenset({"text/html", "application/xhtml+xml"})) -> tuple[bytes, str]:
    """리다이렉트마다 주소를 확인하고 크기 제한 안에서 문서를 읽습니다."""
    deadline = time.monotonic() + seconds
    current_url = url
    for hop in range(MAX_REDIRECTS + 1):
        if time.monotonic() >= deadline:
            raise PageFetchError("timeout", "페이지의 수집 시간이 초과되었습니다.")
        parts, host, port, ip = validate_target(current_url)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise PageFetchError("timeout", "페이지의 수집 시간이 초과되었습니다.")
        # 검증한 IP로 연결하되 HTTPS 인증서와 SNI는 원래 호스트 이름으로 확인합니다.
        if parts.scheme == "https":
            pool = urllib3.HTTPSConnectionPool(ip, port=port, server_hostname=host,
                                               assert_hostname=host, cert_reqs="CERT_REQUIRED")
        else:
            pool = urllib3.HTTPConnectionPool(ip, port=port)
        response = None
        try:
            target = quote(parts.path or "/", safe="/%:@!$&'()*+,;=-._~")
            if parts.query:
                target += "?" + quote(parts.query, safe="%/?@!$&'()*+,;=:-._~")
            host_header = f"[{host}]" if ":" in host else host
            if (parts.scheme, port) not in {("http", 80), ("https", 443)}:
                host_header += f":{port}"
            response = pool.urlopen(
                "GET", target, headers={"Host": host_header,
                    "User-Agent": "CompanyResearchAgent/0.1", "Accept-Encoding": "identity"},
                redirect=False, retries=False, preload_content=False,
                timeout=urllib3.Timeout(total=remaining, connect=min(2, remaining), read=min(2, remaining)),
            )
            if response.status in {301, 302, 303, 307, 308}:
                location = response.headers.get("Location")
                if not location or hop == MAX_REDIRECTS:
                    raise PageFetchError("redirect", "페이지 이동 경로가 없거나 이동 횟수가 초과되었습니다.")
                current_url = urljoin(current_url, location)
                continue
            if not 200 <= response.status < 300:
                raise PageFetchError("http", "페이지가 접근을 허용하지 않거나 HTTP 오류를 반환했습니다.")
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if content_type not in content_types:
                raise PageFetchError("unsupported", "이 문서의 형식은 지원하지 않습니다.")
            encoding = response.headers.get("Content-Encoding", "identity").strip().lower()
            if encoding not in {"", "identity", "gzip"}:
                raise PageFetchError("unsupported", "이 페이지의 압축 형식은 지원하지 않습니다.")
            decoder = zlib.decompressobj(16 + zlib.MAX_WBITS) if encoding == "gzip" else None
            chunks = []
            size = 0
            wire_size = 0
            while True:
                if time.monotonic() >= deadline:
                    raise PageFetchError("timeout", "페이지의 수집 시간이 초과되었습니다.")
                chunk = response.read(16384, decode_content=False)
                if not chunk:
                    break
                wire_size += len(chunk)
                if wire_size > MAX_PAGE_BYTES:
                    raise PageFetchError("too_large", "압축 전송 데이터가 수집 제한을 초과했습니다.")
                # 압축을 풀 때에도 한도를 걸어 작은 압축 파일이 거대한 HTML로 확장되지 않게 합니다.
                if decoder is not None:
                    chunk = decoder.decompress(chunk, MAX_PAGE_BYTES - size + 1)
                size += len(chunk)
                if size > MAX_PAGE_BYTES:
                    raise PageFetchError("too_large", "페이지 크기가 수집 제한을 초과했습니다.")
                chunks.append(chunk)
            if decoder is not None and (not decoder.eof or decoder.unused_data):
                raise PageFetchError("network", "페이지 압축 데이터를 완전히 읽지 못했습니다.")
            return b"".join(chunks), current_url
        except TimeoutError:
            raise PageFetchError("timeout", "페이지의 연결 또는 읽기 시간이 초과되었습니다.") from None
        except (HTTPError, OSError, zlib.error):
            raise PageFetchError("network", "페이지에 연결할 수 없습니다.") from None
        finally:
            if response is not None:
                response.close()
            pool.close()
    raise PageFetchError("redirect", "페이지 이동 횟수가 초과되었습니다.")


def fetch_page(url: str, max_chars: int = MAX_BODY_CHARS, seconds: float = PAGE_SECONDS) -> PageContent:
    html, final_url = fetch_document(url, seconds=seconds)
    title, text, truncated = extract_html(html, max_chars)
    return PageContent(status="success", final_url=final_url, title=title,
                       text=text, truncated=truncated, fetched_at=datetime.now(timezone.utc))


def fetch_job_posting(url: str) -> str:
    # 기존 API의 문자열 반환과 20,000자 제한을 유지합니다.
    return fetch_page(url, max_chars=20000).text
