import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from backend.app.config import ConfigurationError, Settings, load_settings
from backend.app.models import JobAnalysis, ResearchPlan, ResearchQuery
from backend.app.main import generate_research_plan
from backend.app.research import create_research_plan
from backend.app.llm.research_planner import(
    ResearchPlanError,
    create_research_plan_with_openai,
    validate_research_plan,
)

class ResearchPlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.job = JobAnalysis(
            company="테스트회사",
            position="AI Engineer",
            responsibilities=["모델 API 개발"],
            requirements=["Python"],
            preferred=["Docker"],
            keywords=["Python", "Docker"],
        )

        # 기존 Settings 필드와 새 기본값을 사용
        self.settings = Settings(
            use_mock=False,
            llm_provider="openai",
            openai_api_key="unit-test-key",
            openai_model="unit-test-model",
            use_llm_planner=True,
        )

        self.plan = ResearchPlan(
            company=self.job.company,
            position=self.job.position,
            queries=[
                ResearchQuery(
                    topic=f"조사 주제 {index}",
                    query=f"테스트회사 조사 {index}",
                    reason="공고의 업무와 관련된 조사",
                )
                for index in range(5)
            ],
        )

    def test_planner_setting_defaults_and_invalid_value(self) -> None:
        # 실제 .env와 컴퓨터 환경변수를 사용하지 않음
        with (
            patch("backend.app.config.load_dotenv"),
            patch.dict(os.environ, {}, clear=True),
        ) : 
            self.assertFalse(load_settings().use_llm_planner)

            os.environ["USE_LLM_PLANNER"] = "true"
            self.assertTrue(load_settings().use_llm_planner)

            os.environ["USE_LLM_PLANNER"] = "maybe"
            with self.assertRaises(ConfigurationError):
                load_settings()

    def test_rule_mode_does_not_call_llm(self) -> None:
        rule_settings = Settings(
            use_mock=False,
            llm_provider="openai",
            openai_api_key="",
            openai_model="",
        )

        with (
            patch(
                "backend.app.research.load_settings",
                return_value=rule_settings,
            ),
            patch(
                "backend.app.research.create_research_plan_with_openai"
            ) as provider,
        ) : 
            plan = create_research_plan(self.job)

            self.assertEqual(len(plan.queries), 5)
            self.assertEqual(plan.queries[0].topic, "company_business")
            provider.assert_not_called()

    def test_llm_mode_does_not_hide_failure(self) -> None:
        with (
            patch(
                "backend.app.research.load_settings",
                return_value=self.settings,
            ),
            patch(
                "backend.app.research.create_research_plan_with_openai",
                side_effect=ResearchPlanError("timeout", "時間超過")
            ),
            patch(
                "backend.app.research.create_rule_based_research_plan",
            ) as rule,
        ) :
            with self.assertRaises(ResearchPlanError):
                create_research_plan(self.job)

            rule.assert_not_called()

    def test_missing_company_is_rejected_before_settings(self) -> None:
        job = self.job.model_copy(update={"company":""})

        with patch("backend.app.research.load_settings") as load:
            with self.assertRaises(ValueError):
                create_research_plan(job)

            load.assert_not_called()

    def test_original_identity_is_preserved(self) -> None:
        plan = self.plan.model_copy(
            update={"company": "別회사", "position": "別직무"}
        )

        result = validate_research_plan(plan, self.job)

        self.assertEqual(result.company, self.job.company)
        self.assertEqual(result.position, self.job.position)

    def test_invalid_query_counts_are_rejected(self) -> None:
        for count in (0,4,8):
            with self.subTest(count=count):
                plan = self.plan.model_copy(
                    update={"queries": [self.plan.queries[0]] * count}
                )

                with self.assertRaises(ResearchPlanError):
                    validate_research_plan(plan, self.job)

    def test_blank_fields_and_duplicates_are_rejected(self) -> None:
        for field in ("topic", "query", "reason"):
            with self.subTest(field=field):
                queries = list(self.plan.queries)
                queries[0] = queries[0].model_copy(
                    update={field: " "}
                )
                plan = self.plan.model_copy(
                    update={"queries": queries}
                )

                with self.assertRaises(ResearchPlanError):
                    validate_research_plan(plan, self.job)

        # 공백 차이만 있는 검색어도 중복으로 처리
        queries = list(self.plan.queries)
        queries[1] = queries[1].model_copy(
            update={"query": "  테스트회사   조사 0 "}
        )
        plan = self.plan.model_copy(update={"queries": queries})

        with self.assertRaises(ResearchPlanError):
            validate_research_plan(plan, self.job)

    def test_structured_request_and_invalid_responses(self) -> None:
        with patch(
            "backend.app.llm.research_planner.create_openai_client"
        ) as build:
            client = build.return_value.__enter__.return_value
            client.responses.parse.return_value = SimpleNamespace(
                status="completed",
                output=[],
                output_parsed=self.plan,
            )

            result = create_research_plan_with_openai(
                self.job,
                self.settings,
            )

            self.assertEqual(result, self.plan)

            arguments = client.responses.parse.call_args.kwargs
            self.assertIs(arguments["text_format"], ResearchPlan)
            self.assertEqual(
                arguments["input"][1]["content"],
                self.job.model_dump_json()
            )

            # 불완전한 응답·결과 누락·거절을 각각 확인
            responses = [
                SimpleNamespace(
                    status="incomplete",
                    output=[],
                    output_parsed=self.plan,
                ),
                SimpleNamespace(
                    status="completed",
                    output=[],
                    output_parsed=None,
                ),
                SimpleNamespace(
                    status="completed",
                    output=[
                        SimpleNamespace(
                            type="message",
                            content=[SimpleNamespace(type="refusal")],
                        )
                    ],
                    output_parsed=None,
                ),
            ]

            for response in responses:
                with self.subTest(status=response.status):
                    client.responses.parse.return_value = response

                    with self.assertRaises(ResearchPlanError):
                        create_research_plan_with_openai(
                            self.job,
                            self.settings,
                        )

    def test_endpoint_maps_planner_errors(self) -> None:
        for kind, status in (
            ("timeout", 504),
            ("invalid_output", 502),
            ("refusal", 422),
        ) : 
            with self.subTest(kind=kind):
                with patch(
                    "backend.app.main.create_research_plan",
                    side_effect=ResearchPlanError(kind, "테스트 오류"),
                ) : 
                    with self.assertRaises(HTTPException) as caught:
                        generate_research_plan(self.job)

                    self.assertEqual(
                        caught.exception.status_code,
                        status,
                    )

if __name__ == "__main__":
    unittest.main()