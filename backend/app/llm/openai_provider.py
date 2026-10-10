from openai import OpenAI

from backend.app.config import Settings

def create_openai_client(settings: Settings) -> OpenAI:
    """
    설정을 검증한 뒤 OpenAI 클라이언트를 생성합니다.
    """

    # Key 또는 모델명이 없으면 명확한 설정 오류를 발생
    # 모듈 import 시점에는 실행되지 않음
    settings.validate_openai()

    # 클라이언트 생성만 수행
    # 실제 네트워크 요청은 API 메서드를 호출할 때 발생
    return OpenAI(
        api_key=settings.openai_api_key,

        #외부 요청이 무제한 대기하지 않도록 제한
        timeout=30.0,

        # 일시적인 오류의 재시도 횟수를 제한
        max_retries=1,
    )