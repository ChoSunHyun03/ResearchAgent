from collections.abc import Mapping
from urllib.parse import unquote_plus, urlsplit, urlunsplit

from ddgs import DDGS
from ddgs.exceptions import DDGSException, RatelimitException, TimeoutException

from backend.app.models import SearchResult


class SearchError(RuntimeError):
    """외부 검색 실패를 결과 없음과 구분하는 안전한 오류입니다."""

    def __init__(self, kind: str, message: str) -> None:
        super().__init__(message)
        self.kind = kind


def normalize_url(value: object) -> str | None:
    """HTTP(S) 출처를 정리하되 페이지 식별에 필요한 값은 유지합니다."""
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value or any(character.isspace() or ord(character) < 32 for character in value):
        return None
    try:
        parts = urlsplit(value)
        if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
            return None
        if parts.username is not None or parts.password is not None:
            return None
        port = parts.port  # 잘못된 포트 번호도 여기서 검증합니다.
        host = parts.hostname.lower()
        if ":" in host:
            host = f"[{host}]"
        scheme = parts.scheme.lower()
        if port is not None and (scheme, port) not in {("http", 80), ("https", 443)}:
            host = f"{host}:{port}"
        # 일반 추적 값만 제거합니다. id, page, 언어 등 의미 있는 값은 보존합니다.
        parameters = []
        for parameter in parts.query.split("&"):
            key = unquote_plus(parameter.split("=", 1)[0]).lower()
            if key.startswith("utm_") or key in {"gclid", "fbclid", "msclkid"}:
                continue
            # 값의 인코딩과 순서는 그대로 두어 서명 등 의미 있는 값을 보존합니다.
            parameters.append(parameter)
        return urlunsplit((scheme, host, parts.path or "/", "&".join(parameters), ""))
    except ValueError:
        return None


def clean_text(value: object) -> str:
    """잘못된 타입을 문자열로 꾸미지 않고 빈 값으로 처리합니다."""
    return " ".join(value.split()) if isinstance(value, str) else ""


def clean_search_results(raw_results: list, max_results: int = 3) -> list[SearchResult]:
    """순위를 유지하면서 무효 항목과 같은 URL의 중복을 제거합니다."""
    if max_results < 1:
        raise ValueError("검색 결과 개수는 1 이상이어야 합니다.")
    results: list[SearchResult] = []
    seen: dict[str, SearchResult] = {}
    for raw in raw_results:
        if not isinstance(raw, Mapping):
            continue
        url = normalize_url(raw.get("href"))
        title = clean_text(raw.get("title"))
        snippet = clean_text(raw.get("body"))
        if not url or not (title or snippet):
            continue
        if url in seen:
            # 먼저 나온 순위는 유지하고 중복 항목의 누락된 설명만 보완합니다.
            existing = seen[url]
            existing.title = existing.title or title
            existing.snippet = existing.snippet or snippet
            continue
        result = SearchResult(title=title, url=url, snippet=snippet)
        seen[url] = result
        results.append(result)
    return results[:max_results]


def search_web(query: str, max_results: int = 3) -> list[SearchResult]:
    """검색 실패는 예외로 알리고, 정상 검색의 빈 결과는 []로 반환합니다."""
    cleaned_query = clean_text(query)
    if not cleaned_query or max_results < 1:
        raise ValueError("검색어와 검색 결과 개수를 확인해주세요.")
    try:
        # 중복 제거 후에도 세 개를 확보할 수 있도록 후보를 두 배만 요청합니다.
        raw_results = DDGS(timeout=10).text(
            cleaned_query,
            region="kr-kr",
            safesearch="moderate",
            max_results=max_results * 2,
        )
    except TimeoutException:
        raise SearchError("timeout", "검색 시간이 초과되었습니다. 다시 시도해주세요.") from None
    except RatelimitException:
        raise SearchError("rate_limit", "검색 서비스의 요청 제한에 도달했습니다. 잠시 후 다시 시도해주세요.") from None
    except DDGSException:
        # 외부 오류 원문 대신 사용자에게 필요한 메시지만 전달합니다.
        raise SearchError("upstream", "검색 서비스에 연결하지 못했습니다. 다시 시도해주세요.") from None
    if not isinstance(raw_results, list):
        raise SearchError("invalid_response", "검색 서비스가 올바른 결과 목록을 반환하지 않았습니다.")
    return clean_search_results(raw_results, max_results)
