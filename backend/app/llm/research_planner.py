from backend.app.llm.usage import record_usage
from openai import(
    APIError,
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    PermissionDeniedError,
    RateLimitError,
)

from backend.app.config import Settings
from backend.app.models import JobAnalysis, ResearchPlan, ResearchQuery
from backend.app.prompts import RESEARCH_PLAN_PROMPT
from backend.app.llm.openai_provider import create_openai_client

class ResearchPlanError(RuntimeError):
    """
    계획 생성 오류의 유형과 안전한 메세지입니다.
    """

    def __init__(self, kind: str, message: str) -> None:
        super().__init__(message)
        self.kind = kind

def validate_research_plan(
        plan: ResearchPlan,
        job_analysis: JobAnalysis,
) -> ResearchPlan:
    """
    검색 개수·빈 항목·동일 검색어 증복을 확인합니다.
    """

    if not 5 <= len(plan.queries) <= 7:
        raise ResearchPlanError(
            "invalid_output",
            "조사 항목은 5개 이상 7개 이하여야 합니다.",
        )

    queries = []
    seen_qeuries = set()

    for item in plan.queries:
        # 앞뒤 공백과 검색어 내부의 연속 공백을 정리
        topic = item.topic.strip()
        query = " ".join(item.query.split())
        reason = item.reason.strip()

        if not topic or not query or not reason:
            raise ResearchPlanError(
                "invalid_output",
                "조사 주제·검색어·조사 이유에 빈 값이 있습니다.",
            )

        # 대소문자와 공백 차이만 있는 동일 검색어도 중복으로 인식
        # 의미가 비슷한 검색어까지 판정하는 기능은 아님
        query_key = query.casefold()

        if query_key in seen_qeuries:
            raise ResearchPlanError(
                "invalid_output",
                "동일한 검색어가 중복되었습니다.",
            )

        seen_qeuries.add(query_key)
        queries.append(
            ResearchQuery(
                topic=topic,
                query=query,
                reason=reason,
            )
        )

    # 회사명·직무명은 모델이 생성한 값 대신 원본 입력을 사용
    return ResearchPlan(
        company=job_analysis.company,
        position=job_analysis.position,
        queries=queries,
    )

def create_research_plan_with_openai(
        job_analysis: JobAnalysis,
        settings: Settings,
) -> ResearchPlan:
    """
    공고 분석 결과를 기존 ResearchPlan으로 변환합니다.
    """

    settings.validate_openai()

    try:
        with create_openai_client(settings) as client:
            response = client.responses.parse(
                model=settings.openai_model,
                input=[
                    {
                        "role": "system",
                        "content" : RESEARCH_PLAN_PROMPT,
                    },
                    {
                        # 여섯 필드를 모두 JSON 데이터로 전달
                        # 입력을 직렬화하는 것이며 응답 수동 파싱이 아님
                        "role" : "user",
                        "content" : job_analysis.model_dump_json(),
                    },
                ],
                text_format=ResearchPlan,
                max_output_tokens=3000,
                store=False,
            )

    except APITimeoutError:
        raise ResearchPlanError(
            "timeout",
            "조사 계획 생성 시간이 초과되었습니다.",
        ) from None

    except RateLimitError:
        raise ResearchPlanError(
            "rate_limit",
            "OpenAI 호출 제한 또는 사용 한도를 확인해주세요.",
        ) from None

    except (AuthenticationError, PermissionDeniedError):
        raise ResearchPlanError(
            "authentication",
            "OpenAI API Key 또는 접근 권한을 확인해주세요.",
        ) from None

    except APIConnectionError:
        raise ResearchPlanError(
            "connection",
            "OpenAI 서버에 연결할 수 없습니다.",
        ) from None

    except APIError:
        raise ResearchPlanError(
            "upstream",
            "조사 계획 요청이 실패했습니다. 모델과 서비스 상태를 확인해주새요.",
        ) from None

    except ValueError:
        raise ResearchPlanError(
            "invalid_output",
            "조사 계획 응답을 해석하지 못했습니다.",
        ) from None

    record_usage(response, settings.openai_model, "research_plan")

    for item in response.output:
        if item.type == "message":
            for content in item.content:
                if content.type == "refusal":
                    raise ResearchPlanError(
                        "refusal",
                        "모델이 조사 계획 생성을 거절했습니다.",
                    )

    if response.status != "completed":
        raise ResearchPlanError(
            "invalid_output",
            "조사 계획이 응답이 완성되지 않았습니다.",
        )

    plan = response.output_parsed

    if not isinstance(plan, ResearchPlan):
        raise ResearchPlanError(
            "invalid_output",
            "유효한 ResearchPlan 결과가 없스니다."
        )

    return validate_research_plan(plan, job_analysis)