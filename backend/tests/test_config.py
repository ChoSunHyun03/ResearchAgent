import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from backend.app.config import ConfigurationError, load_settings
from backend.app.llm.openai_provider import create_openai_client

class SettingsTest(unittest.TestCase):
    def setUp(self) -> None:
        # 실제 프로젝트 .env를 수정하지 않는 임시 폴더
        self.temp_dir = TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.env_file = Path(self.temp_dir.name) / ".env"

        # 테스트에서는 임시 .env만 읽도록 경로를 바꿈
        env_path_patch = patch(
            "backend.app.config.ENV_FILE",
            self.env_file,
        )
        env_path_patch.start()
        self.addCleanup(env_path_patch.stop)

        # 컴퓨터의 실제 환경변수와 Key가 테스트에 섞이지 않게 함
        environment_patch = patch.dict(
            os.environ,
            {},
            clear=True,
        )
        environment_patch.start()
        self.addCleanup(environment_patch.stop)
    
    def write_env(self,content: str) -> None:
        # 입력받은 문자열을 테스트용 임시 .env에 작성
        self.env_file.write_text(content, encoding="utf-8")

    def test_defaults_keep_mock_without_key(self) -> None:
        # .env가 없어도 기본 mock 설정을 읽을 수 있는지 확인 
        settings = load_settings()

        self.assertTrue(settings.use_mock)
        self.assertEqual(settings.llm_provider, "openai")
        self.assertEqual(settings.openai_api_key, "")
        self.assertEqual(settings.openai_model, "")

    def test_loads_env_and_hides_key_in_repr(self) -> None:
        # 아래 Key는 테스트용 문자열이며 실제 Key가 아닙니다.
        self.write_env(
            "USE_MOCK=false\n"
            "LLM_PROVIDER=openai\n"
            "OPENAI_API_KEY=unit-test-key\n"
            "OPENAI_MODEL=unit-test-model\n"
        )

        settings = load_settings()

        self.assertFalse(settings.use_mock)
        self.assertEqual(settings.openai_model,"unit-test-model")
        self.assertEqual(settings.openai_api_key,"unit-test-key")

        # 설정 객체 출력에 Key가 포함되지 않는지 확인
        self.assertNotIn("unit-test-key",repr(settings))

    def test_system_environment_has_priority(self) -> None:
        self.write_env(
            "USE_MOCK=false\n"
            "OPENAI_MODEL=file-model\n"
        )

        # 시스템 환경변수가 .env보다 우선해야 함
        os.environ["USE_MOCK"] = "true"
        os.environ["OPENAI_MODEL"] = "system-model"

        settings = load_settings()

        self.assertTrue(settings.use_mock)
        self.assertEqual(settings.openai_model,"system-model")

    def test_invalid_mock_value_is_rejected(self) -> None:
        self.write_env("USE_MOCK=maybe\n")

        with self.assertRaisesRegex(
            ConfigurationError,
            "USE_MOCK",
        ):
            load_settings()

    def test_unsupported_provider_is_rejected(self) -> None:
        # 지원하지 않는 Provider를 테스트용 .env에 작성
        self.write_env("LLM_PROVIDER=unsupported\n")

        # 잘못된 Provider 설정이 명확한 오류로 처리되는지 확인
        with self.assertRaisesRegex(
            ConfigurationError,
            "LLM_PROVIDER",
        ) :
            load_settings()

    def test_missing_key_is_rejected_before_client_creation(self) -> None:
        self.write_env("OPENAI_MODEL=unit-test-model\n")

        # SDK 클라이언트를 대체해 실제 생성이나 호출을 막음
        with patch(
            "backend.app.llm.openai_provider.OpenAI"
        ) as client_class:
            with self.assertRaisesRegex(
                ConfigurationError,
                "OPENAI_API_KEY",
            ):
                create_openai_client(load_settings())

            client_class.assert_not_called()

    def test_missing_model_is_rejected(self) -> None:
        self.write_env("OPENAI_API_KEY=unit-test-key\n")

        with self.assertRaisesRegex(
            ConfigurationError,
            "OPENAI_MODEL",
        ):
            load_settings().validate_openai()

    def test_client_receives_validated_settings(self) -> None:
        self.write_env(
            "OPENAI_API_KEY=unit-test-key\n"
            "OPENAI_MODEL=unit-test-model\n"
        )

        # 실제 SDK 대신 객체로 생성 인자를 검증
        with patch(
            "backend.app.llm.openai_provider.OpenAI"
        ) as client_class:
            client = create_openai_client(load_settings())

            client_class.assert_called_once_with(
                api_key="unit-test-key",
                timeout=30.0,
                max_retries=1,
            )

            self.assertIs(client, client_class.return_value)

if __name__ == "__main__":
    # 파일을 직접 실행해도 테스트를 실행할 수 있음
    unittest.main()