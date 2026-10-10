from openai import (
    OpenAI,
    APIError,
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    PermissionDeniedError,
    RateLimitError,
)

from backend.app.config import Settings
from backend.app.models import JobAnalysis
from backend.app.prompts import JOB_ANALYSIS_PROMPT

class JobAnalysisError(RuntimeError):
    """
    분석 실패 유형과 사용자에게 전달할 안전한 메세지입니다.
    """

    def __init__(self, kind: str, message: str) -> None:
        super().__init__(message)
        self.kind = kind


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

def analyze_job_with_openai(job_text: str, settings: Settings) -> JobAnalysis:
    """
    실제공고를 분석하여 기존 Pydantic 모델로 반환합니다.
    """

    # 설정 오류를 외부 API 오류와 구분
    settings.validate_openai()

    try:
        # 요청 후 클라이언트릐 연결 자원을 정리
        with create_openai_client(settings) as client:
            response = client.responses.parse(
                model=settings.openai_model,
                input=[
                    {
                        "role": "system",
                        "content": JOB_ANALYSIS_PROMPT,
                    },
                    {
                        # 분석 규칙과 공고 데이터를 분리
                        "role": "user",
                        "content": job_text,
                    },
                ],
                # 수동 JSON 파싱 대신 기존 Pydantic 모델을 사용
                text_format=JobAnalysis,
                max_output_tokens=2000,
                store=False,
            )

    # timeout은 연결 오류보다 먼저 처리
    except APITimeoutError:
        raise JobAnalysisError(
            "timeout",
            "채용공고 분석 요청 시간이 초과되었습니다.",
        ) from None

    except RateLimitError:
        raise JobAnalysisError(
            "rate_limit",
            "OpenAI 호출 제한 또는 사용 한도를 확인해주세요.",
        ) from None

    except (AuthenticationError, PermissionDeniedError):
        raise JobAnalysisError(
            "authentication",
            "OpenAI API KEY 또는 접근 권한을 확인헤주세요.",
        ) from None

    except APIConnectionError:
        raise JobAnalysisError(
            "connection",
            "OpenAI 서버에 연결할 수 없습니다.",
        ) from None

    except APIError:
        # SDK 오류 원문이나 요청 내용을 사용자에게 노출하지 않음
        raise JobAnalysisError(
            "upstream",
            "OpenAI 요청이 실패했습니다. 모델 설정과 서비스 상태를 확인해주세요.",
        ) from None

    except ValueError:
        # SDK의 JSON·Pydantic 파싱 실패을 안전하게 처리합니다.
        raise JobAnalysisError(
            "invalid_output",
            "분석 결과를 JobAnalysis 형식으로 해석하지 못했습니다.",
        ) from None

    # 거절 응답은 일반 분석 결과와 구분
    for item in response.output:
        if item.type == "message":
            for content in item.content:
                if content.type == "refusal":
                    raise JobAnalysisError(
                        "refusal",
                        "모델이 이 입력에 대한 분석을 거절했습니다.",
                    )

    # 토큰 제한 등으로 중단된 응답을 정상 결과로 사용하지 않음
    if response.status != "completed":
        raise JobAnalysisError(
            "invalid_output",
            "분석 응답이 완성되지 않았습니다.",
        )

    result = response.output_parsed
    if not isinstance(result, JobAnalysis):
        raise JobAnalysisError(
            "invalid_output",
            "유효한 JobAnalysis 결과가 없습니다.",
        )

    return result