from ddgs import DDGS
from ddgs.exceptions import DDGSException

from backend.app.models import SearchResult

def search_web(query: str, max_results: int = 3) -> list[SearchResult]:
    """
    검색 Qeury를 받아 실제 웹 검색을 수행한다. 

    현재 Qeury당 최대 3개의 결과만 반환한다.
    """
    try:
        #DDGS를 이용해 텍스트 검색 수행
        results = DDGS().text(
            query,
            region="kr-kr",
            safesearch="moderate",
            max_results=max_results,
        )

        search_results = []

        # 검색 결과를 SearchResult 형태로 변환
        for result in results:
            search_results.append(
                SearchResult(
                    title=result.get("title",""),
                    url=result.get("href",""),
                    snippet=result.get("body",""),
                )
            )

        return search_results

    except DDGSException as error:
        # 검색 결과가 없거나 DDGS 검색 자체가 실패한 경우
        print(f"[검색 실패] query={query}")
        print(f"[DDGS 오류] {error}")

        #예외를 다시 던지지 않고 빈 결과 반환

        return []
