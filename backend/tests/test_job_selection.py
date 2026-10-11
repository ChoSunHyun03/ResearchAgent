import asyncio
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.app.config import Settings
from backend.app.llm.openai_provider import analyze_job_with_openai
from backend.app.models import JobAnalysis, JobInput
from backend.app.research import analyze_job, create_research_plan, finalize_job_analysis
from backend.tests.test_web_research import post_json


def analysis(**updates):
    values = dict(company="가상회사", position="AI Engineer", responsibilities=["모델 개발"],
                  requirements=["Python"], preferred=[], keywords=["Python"])
    values.update(updates)
    return JobAnalysis(**values)


def settings(mock=False):
    return Settings(use_mock=mock, llm_provider="openai", openai_api_key="test", openai_model="test")


class JobSelectionTests(unittest.TestCase):
    def test_old_request_and_result_defaults_are_preserved(self):
        self.assertEqual(JobInput(job_text="공고").target_position, "")
        result = analysis()
        self.assertEqual(result.analysis_status, "ready")
        self.assertEqual(finalize_job_analysis(result), result)

    def test_multiple_roles_without_selection_clear_mixed_conditions(self):
        result = finalize_job_analysis(analysis(available_positions=["AI Engineer", "AX PM"]))
        self.assertEqual(result.analysis_status, "needs_selection")
        self.assertEqual(result.available_positions, ["AI Engineer", "AX PM"])
        self.assertEqual(result.position, "")
        self.assertEqual(result.responsibilities, [])
        self.assertEqual(result.requirements, [])
        self.assertEqual(result.keywords, [])

    def test_selected_role_reaches_provider(self):
        with patch("backend.app.research.load_settings", return_value=settings()), patch("backend.app.research.analyze_job_with_openai", return_value=analysis(available_positions=["AI Engineer", "AX PM"])) as provider:
            result = analyze_job("  여러 직무 공고  ", " AI Engineer ")
        provider.assert_called_once_with("여러 직무 공고", settings(), "AI Engineer")
        self.assertEqual(result.analysis_status, "ready")
        self.assertEqual(result.requirements, ["Python"])

    def test_selection_is_passed_as_data_to_structured_output(self):
        with patch("backend.app.llm.openai_provider.create_openai_client") as build:
            client = build.return_value.__enter__.return_value
            client.responses.parse.return_value = SimpleNamespace(status="completed", output=[], output_parsed=analysis())
            analyze_job_with_openai("공고 원문", settings(), "AI Engineer")
            arguments = client.responses.parse.call_args.kwargs
        self.assertIs(arguments["text_format"], JobAnalysis)
        self.assertEqual(json.loads(arguments["input"][1]["content"]), {"job_text": "공고 원문", "target_position": "AI Engineer"})

    def test_unknown_or_wrong_selected_role_is_not_used(self):
        original = analysis(available_positions=["AI Engineer", "AX PM"])
        for target, expected in (("영업", "needs_selection"), ("AX PM", "missing_details")):
            with self.subTest(target=target):
                result = finalize_job_analysis(original, target)
                self.assertEqual(result.analysis_status, expected)
                self.assertEqual(result.position, "")
                self.assertEqual(result.requirements, [])

    def test_missing_details_are_not_replaced_by_generic_job_knowledge(self):
        result = finalize_job_analysis(analysis(position="", analysis_status="missing_details", analysis_message="상세 공고 필요"), "AI Engineer")
        self.assertEqual(result.analysis_status, "missing_details")
        self.assertEqual(result.responsibilities, [])
        self.assertEqual(result.analysis_message, "상세 공고 필요")

    def test_unresolved_analysis_cannot_start_planner(self):
        with patch("backend.app.research.load_settings") as load:
            with self.assertRaises(ValueError):
                create_research_plan(analysis(analysis_status="needs_selection"))
        load.assert_not_called()

    def test_http_initial_selection_and_selected_reanalysis(self):
        first = analysis(available_positions=["AI Engineer", "AX PM"])
        with patch("backend.app.research.load_settings", return_value=settings()), patch("backend.app.research.analyze_job_with_openai", return_value=first):
            status, result = asyncio.run(post_json("/api/jobs/analyze", {"job_text": "여러 직무 공고"}))
            self.assertEqual(status, 200)
            self.assertEqual(result["analysis_status"], "needs_selection")
            status, selected = asyncio.run(post_json("/api/jobs/analyze", {"job_text": "여러 직무 공고", "target_position": "AI Engineer"}))
            self.assertEqual(status, 200)
            self.assertEqual(selected["analysis_status"], "ready")
            self.assertEqual(selected["position"], "AI Engineer")
        status, _ = asyncio.run(post_json("/api/research/plan", result))
        self.assertEqual(status, 422)

    def test_mock_does_not_override_explicit_target_and_long_target_is_rejected(self):
        with patch("backend.app.research.load_settings", return_value=settings(mock=True)), patch("backend.app.research.load_mock_analysis", return_value=analysis()), patch("backend.app.research.analyze_job_with_openai") as provider:
            result = analyze_job("공고", "AX PM")
            self.assertEqual(result.analysis_status, "needs_selection")
            provider.assert_not_called()
        with patch("backend.app.research.load_settings") as load:
            with self.assertRaises(ValueError):
                analyze_job("공고", "가" * 121)
            load.assert_not_called()

    def test_hiring_category_is_not_a_position_candidate(self):
        for target in ("", "AI Engineer"):
            with self.subTest(target=target):
                result = finalize_job_analysis(analysis(position="Junior Talent", available_positions=["Junior Talent"]), target)
                self.assertEqual(result.analysis_status, "missing_details")
                self.assertEqual(result.available_positions, [])
                self.assertEqual(result.position, "")
                self.assertEqual(result.requirements, [])
