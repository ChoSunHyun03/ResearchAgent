from ddgs import DDGS

from backend.app.models import SearchResult

def search_web(query: str, max_results: int = 3) -> list[SearchResult]:
    """
    검색 Qeury를 받아 실제 웹 검색을 수행한다. 

    현재 Qeury당 최대 3개의 결과만 반환한다.
    """

    results = DDGS().text(
        query,
        region="kr-kr",
        safesearch="moderate",
        max_results=max_results
    )

    search_results = []

    for result in results:
        search_results.append(
            SearchResult(
                title=result.get("title",""),
                url=result.get("href",""),
                snippet=result.get("body",""),
            )
        )

    return search_results