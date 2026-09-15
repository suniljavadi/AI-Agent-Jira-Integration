from fastapi import Header, HTTPException

from app.config import get_settings


def require_auth(authorization: str | None = Header(default=None)) -> str:
    settings = get_settings()
    if settings.app_env == "development" and not authorization:
        return "demo-user"
    if authorization != f"Bearer {settings.api_token}":
        raise HTTPException(status_code=401, detail="Invalid or missing bearer token")
    return "demo-user"
