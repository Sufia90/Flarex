from pydantic_settings import BaseSettings, SettingsConfigDict


class AISettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AI_", extra="ignore")

    provider: str | None = None
    api_key: str | None = None
    model: str | None = None
    evidence_grounded: bool = True
    enabled: bool = False

    @property
    def is_configured(self) -> bool:
        return self.provider is not None and self.api_key is not None


def get_ai_settings() -> AISettings:
    return AISettings()
