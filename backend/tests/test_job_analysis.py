import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from backend.app.config import ConfigurationError, Settings
from backend.app.models import JobAnalysis, JobInput
from backend.app.main import analyze_job_posting
from backend.app.research import analyze_job
from backend.app.llm.openai_provider import (
    JobAnalysisError,
    analyze_job_with_openai
)

class JobAnalysisTests(unittest.TestCase):
    def setUp(self) -> None:
        # 실제 Key가 아닌 테스트용 설정
        self.settings = Settings(
            use_mock=False,
            llm_provider="openai",
            openai_api_key="unit-test-key",
            openai_model="unit-test-model",
        )

        self.result = JobAnalysis(
            company="테스트회사",
            position="AI Engineer",
            responsibilities=["모델 API 개발"],
            requirements=["Python"],
            preferred=[],
            keywords=["Python"],
        )

    def test_empty_input_is_rejected_before_loading_settings(self) -> None:
        # 빈 입력은 설정 로딩과 API 호출 전에 차단해야 함
        with patch("backend.app.research.load_settings") as load:
            for text in (""," ","\n\t"):
                with self.subTest(text=text):
                    with self.assertRaises(ValueError):
                        analyze_job(text)

            load.assert_not_called()

    def test_too_long_input_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            analyze_job("가"*20001)

    def test_mock_mode_does_not_call_openai(self) -> None:
        mock_settings = Settings(
            use_mock=True,
            llm_provider="openai",
            openai_api_key="",
            openai_model="",
        )

        with (
            patch(
                "backend.app.research.load_settings",
                return_value=mock_settings,
            ),
            patch(
                "backend.app.research.load_mock_analysis",
                return_value=self.result,
            ),
            patch(
                "backend.app.research.analyze_job_with_openai"
            ) as provider,
        ) : 
            self.assertEqual(analyze_job("공고"), self.result)
            provider.assert_not_called()

    def test_openai_mode_receives_cleaned_input(self) -> None:
        with(
            patch(
                "backend.app.research.load_settings",
                return_value=self.settings,
            ),
            patch(
                "backend.app.research.analyze_job_with_openai",
                return_value=self.result,
            ) as provider,
        ) :
            self.assertEqual(analyze_job(" 실제 공고 "), self.result)
            provider.assert_called_once_with(
                "실제 공고",
                self.settings,
            )

    def test_structured_output_uses_existing_model(self) -> None:
        with patch(
            "backend.app.llm.openai_provider.create_openai_client"
        ) as build:
            # with 문이 반환할 테스트용 클라이언트입니다.
            client = build.return_value.__enter__.return_value
            client.responses.parse.return_value = SimpleNamespace(
                status="completed",
                output=[],
                output_parsed=self.result,
            )

            result = analyze_job_with_openai(
                "테스트 공고",
                self.settings,
            )

            self.assertEqual(result, self.result)

            arguments = client.responses.parse.call_args.kwargs
            self.assertIs(arguments["text_format"], JobAnalysis)
            self.assertEqual(
                arguments["input"][1]["content"],
                "테스트 공고",
            )

    def test_missing_parsed_output_is_rejected(self) -> None:
        with patch(
            "backend.app.llm.openai_provider.create_openai_client"
        ) as build:
            # 실제 API 대신 파싱 결과가 없는 응답을 만듬
            client = build.return_value.__enter__.return_value
            client.responses.parse.return_vaule = SimpleNamespace(
                status="completed",
                output=[],
                output_parsed=None,
            )

            with self.assertRaises(JobAnalysisError) as caught:
                analyze_job_with_openai("공고", self.settings)

            # 결과 누락을 출력 오류로 처리하는지 확인
            self.assertEqual(caught.exception.kind, "invalid_output")

    def test_incomplete_output_is_rejected(self) -> None:
        with patch(
            "backend.app.llm.openai_provider.create_openai_client"
        ) as build:
            # 파싱 결과가 있어도 응답이 미완성이라면 거부
            client = build.return_value.__enter__.return_value
            client.responses.parse.return_value = SimpleNamespace(
                status="incomplete",
                output=[],
                output_parsed=self.result,
            )

            with self.assertRaises(JobAnalysisError) as caught:
                analyze_job_with_openai("공고", self.settings)

            self.assertEqual(caught.exception.kind, "invalid_output")

    def test_refusal_is_distinguished(self) -> None:
        with patch(
            "backend.app.llm.openai_provider.create_openai_client"
        ) as build:
            client = build.return_value.__enter__.return_value
            client.responses.parse.return_value = SimpleNamespace(
                status="completed",
                output=[
                    SimpleNamespace(
                        type="message",
                        content=[
                            SimpleNamespace(type="refusal")
                        ],
                    )
                ],
                output_parsed=None,
            )

            with self.assertRaises(JobAnalysisError) as caught:
                analyze_job_with_openai("공고", self.settings)

            self.assertEqual(caught.exception.kind, "refusal")

    def test_endpoint_returns_422_for_empty_input(self) -> None:
        # HTTP 서버 없이 라우트 함수의 오류 변환을 확인
        with self.assertRaises(HTTPException) as caught:
            analyze_job_posting(JobInput(job_text=" "))

        self.assertEqual(caught.exception.status_code, 422)

    def test_endpoint_returns_503_for_missing_configuration(self) -> None:
        with patch(
            "backend.app.main.analyze_job",
            side_effect=ConfigurationError(
                "OPENAI_API_KEY가 설정되지 않았습니다."
            ),
        ) :
            with self.assertRaises(HTTPException) as caught:
                analyze_job_posting(JobInput(job_text="공고"))

            self.assertEqual(caught.exception.status_code, 503)

if __name__ == "__main__":
    unittest.main()