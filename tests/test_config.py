import pytest
from pydantic import ValidationError

from app.config import Settings


def test_production_rejects_default_or_short_api_token():
    with pytest.raises(ValidationError):
        Settings(app_env="production", _env_file=None)

    with pytest.raises(ValidationError):
        Settings(app_env="production", api_token="short-token", _env_file=None)


def test_production_accepts_long_api_token():
    settings = Settings(
        app_env="production",
        api_token="x" * 32,
        _env_file=None,
    )

    assert settings.app_env == "production"
