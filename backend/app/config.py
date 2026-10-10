import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# config.py 위치를 기준으로 프로젝트 루트를 계산
# 터미널의 현재 위치에 따라 다른 .env를 읽는 것을 방지
PROJECT_ROOT = Path(__file__).resolve().parents[2]


# 프로젝트 루트의 .env만 읽음
ENV_FILE = PROJECT_ROOT / ".env"

class ConfigurationError(ValueError):
    """
    환경설정이 잘못되었을 때 사용하는 오류입니다. 
    """

def parse_bool(value: str, variable_name: str) -> bool:
    """
    환경변수의 문자열을 명확한 bool 값으로 변환합니다.
    """

    # 대소문자의 앞뒤 공백을 정리
    normalized= value.strip().lower()

    if normalized == "true":
        return True

    if normalized == "false":
        return False

    # 잘못된 값을 조용히 False로 처리하지 않음
    # 오류 메세지에는 입력값을 포함하지 않음
    raise ConfigurationError(
        f"{variable_name}는 true 또는 false여야 합니다."
    )

@dataclass(frozen=True)
class Settings:
    """
    한 번 읽은 설정값을 변경하지 않는 객체입니다.
    """

    use_mock: bool
    llm_provider: str

    # 객체를 출력해도 API Key가 repr에 표시되지 않도록
    openai_api_key: str = field(repr=False)

    openai_model : str

    def validate_openai(self) -> None:
        """
        OpenAI 클라이언트를 만들기 전에 필요한 설정을 검증합니다.
        """

        if self.llm_provider != "openai":
            raise ConfigurationError(
                "현재 지원하는 LLM_PROVIDER는 openai입니다."
            )
        
        if not self.openai_api_key:
            raise ConfigurationError(
                "OPENAI_API_KEY가 설정되지 않았습니다."
            )

        if not self.openai_model:
            raise ConfigurationError(
                "OPENAI_MODEL이 설정되지 않았습니다."
            )

def load_settings() -> Settings:
    """
    루트 .env와 시스템 환경변수에서 설정을 읽습니다.
    """

    # 이미 설정된 시스템 환경변수가 .env보다 우선
    # 파일이 없어도 기본값으로 mock 환경을 준비할 수 있음
    load_dotenv(
        dotenv_path=ENV_FILE,
        override=False,
        encoding="utf-8",
    )

    # 기본값은 기존 공작을 유지하느 mock 모드
    use_mock = parse_bool(
        os.getenv("USE_MOCK", "true"),
        "USE_MOCK",
    )

    # 현재 지원하는 Provider 이름을 검증
    llm_provider = os.getenv(
        "LLM_PROVIDER",
        "openai"
    ).strip().lower()

    if llm_provider != "openai":
        raise ConfigurationError(
            "현재 지원하는 LLM_PROVIDER는 openai입니다."
        )

    # Key와 모델명은 여기서 빈 값도 허용
    # 실제 OpenAI 사용 시 validate_openai()가 확인
    return Settings(
        use_mock=use_mock,
        llm_provider=llm_provider,
        openai_api_key=os.getenv("OPENAI_API_KEY","").strip(),
        openai_model=os.getenv("OPENAI_MODEL","").strip(),
    )

