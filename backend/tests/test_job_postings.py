import asyncio
import json
import unittest
from unittest.mock import patch

from backend.app.job_postings import parse_jd_data, build_roles, fetch_job_details
from backend.app.models import JobPosting
from backend.app.scraper import PageFetchError
from backend.tests.test_web_research import post_json

LABELS = ["[직무기술]", "[자격 요건]", "[필요 역량]", "[우대사항]"]
URL = "https://skbroadband-juniortalent.co.kr/"
HTML = b'<html><main>company</main><script src="/assets/js/data/jd-data.js?v=1"></script></html>'


def fixture(count=2):
    return {"tabs": [{"id": "a", "title": "직군", "link": "https://example.com/apply"}],
            "detailLabels": LABELS, "items": {"a": [
                {"id": f"role{i}", "title": f"직무{i}", "details": [
                    [f"업무{i}"], [f"자격{i}"], [f"역량{i}"], [f"우대{i}"]]}
                for i in range(count)]}}


def script(data):
    return "const JDDataStore = " + json.dumps(data, ensure_ascii=False)


class JobPostingTests(unittest.TestCase):
    def test_variable_count_and_role_isolation(self):
        for count in (1, 3, 12):
            roles = build_roles(parse_jd_data(script(fixture(count))), "학사 이상", "회사", URL)
            self.assertEqual(len(roles), count)
            for i, role in enumerate(roles):
                self.assertEqual(role.competencies, [f"역량{i}"])
                self.assertIn("학사 이상", role.analysis_text)
                self.assertEqual(role.preferred, [f"우대{i}"])
                if count > 1:
                    self.assertNotIn(f"업무{(i+1)%count}", role.analysis_text)

    def test_js_literals_comments_trailing_comma_and_methods(self):
        text = "const JDDataStore = {tabs:[{id:'a',title:'직군',active:true,},], /* comment */ detailLabels:" + json.dumps(LABELS) + ",items:{a:[]}, getData:function(){ throw Error('do not execute'); }};"
        data = parse_jd_data(text)
        self.assertEqual(data["tabs"][0]["title"], "직군")
        self.assertEqual(data["items"], {"a": []})

    def test_executable_value_duplicate_keys_and_truncated_data_rejected(self):
        for text in ["const JDDataStore = {tabs:evil()}", "const JDDataStore = {tabs:[],tabs:[]}",
                     "const JDDataStore = {tabs:['unfinished", "no data"]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_jd_data(text)

    def test_semantic_schema_and_duplicate_ids_rejected(self):
        data = fixture()
        data["detailLabels"] = list(reversed(LABELS))
        with self.assertRaises(ValueError):
            parse_jd_data(script(data))
        data = fixture()
        data["items"]["a"][1]["id"] = "role0"
        with self.assertRaises(ValueError):
            build_roles(data, "", "회사", URL)

    def test_grouped_details_preserve_subheading(self):
        data = fixture(1)
        data["items"]["a"][0]["details"][0] = [{"title": "부문", "list": ["업무"]}]
        self.assertEqual(build_roles(data, "", "회사", URL)[0].responsibilities, ["부문: 업무"])

    def test_html_and_js_are_fetched_without_model_call(self):
        with patch("backend.app.job_postings.fetch_document", side_effect=[(HTML, URL), (script(fixture()).encode(), URL)]) as fetch:
            result = fetch_job_details(URL)
        self.assertEqual(len(result.roles), 2)
        self.assertTrue(fetch.call_args.args[0].endswith("jd-data.js?v=1"))
        self.assertIn("application/javascript", fetch.call_args.kwargs["content_types"])

    def test_failure_preserves_original_with_warning_and_no_wrong_roles(self):
        with patch("backend.app.job_postings.fetch_document", side_effect=[(HTML, URL), PageFetchError("timeout", "timeout")]):
            result = fetch_job_details(URL)
        self.assertEqual(result.roles, [])
        self.assertIn("company", result.job_text)
        self.assertTrue(result.warnings)

    def test_cross_origin_script_is_not_requested(self):
        html = HTML.replace(b'/assets/js/', b'https://evil.example/assets/js/')
        with patch("backend.app.job_postings.fetch_document", return_value=(html, URL)) as fetch:
            result = fetch_job_details(URL)
        self.assertEqual(fetch.call_count, 1)
        self.assertEqual(result.roles, [])

    def test_unknown_site_retains_generic_flow(self):
        with patch("backend.app.job_postings.fetch_document", return_value=(HTML, "https://example.com/")) as fetch:
            result = fetch_job_details("https://example.com/")
        self.assertEqual(result.roles, [])
        self.assertEqual(fetch.call_count, 1)

    def test_endpoint_returns_roles_without_analyzing(self):
        roles = build_roles(fixture(), "", "회사", URL)
        with patch("backend.app.main.fetch_job_details", return_value=JobPosting(job_text="원문", roles=roles)), patch("backend.app.main.analyze_job") as analyze:
            status, body = asyncio.run(post_json("/api/jobs/fetch", {"job_url": URL}))
        self.assertEqual(status, 200)
        self.assertEqual(body["job_text"], "원문")
        self.assertEqual(len(body["roles"]), 2)
        analyze.assert_not_called()
