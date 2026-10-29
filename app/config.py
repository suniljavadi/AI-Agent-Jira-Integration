from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    mock_mode: bool = True
    database_url: str = "sqlite:///./ai_jira.db"
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str = "gpt-4o-mini"
    api_token: str = "dev-token"
    approval_ttl_minutes: int = 30
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.app_env.casefold() == "production" and (
            self.api_token == "dev-token" or len(self.api_token) < 32
        ):
            raise ValueError("Production requires an API_TOKEN of at least 32 characters")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
