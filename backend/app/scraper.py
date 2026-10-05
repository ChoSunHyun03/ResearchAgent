import requests

from bs4 import BeautifulSoup

def fetch_job_posting(url: str) -> str:
    """
    채용공고 URL에 접속하여 
    페이지의 텍스트 내용을 추출한다.

    현재 requests + Beautifulsoup 기반으로 구현

    JavaScript로 동적 렌더링되는 페이지는 
    정상적으로 내용을 가져오지 못할 수 있다.
    """

    # 실제 브라우저처럼 보이도록 User-Agent 설정
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/140.0 Safari/537.36"
        )
    }

    #URL에 GET 요청
    response = requests.get(
        url,
        headers=headers,
        timeout = 10,
    )

    # HTTP 오류가 있으면 예외 발생
    response.raise_for_status()

    #HTML을 BeautifulSoup으로 파싱
    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    # script, style 등 채용공고 분석에 필요 없는 요소 제거
    for tag in soup(["script","style","noscript"]):
        tag.decompose()

    # 페이지 전체 텍스트 추출
    text = soup.get_text(
        separator="\n",
        strip=True,
    )

    # 너무 긴 경우 MVP 단계에서는 앞부분만 사용
    return text[:20000]