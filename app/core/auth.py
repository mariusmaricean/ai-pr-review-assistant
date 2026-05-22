from fastapi import Header, HTTPException

from app.config import settings


def _clean_token(token: str | None) -> str:
    return (token or "").strip().strip('"').strip("'")


def verify_admin_token(x_admin_token: str | None = Header(default=None)):
    configured_token = _clean_token(settings.admin_api_token)
    provided_token = _clean_token(x_admin_token)

    if not configured_token:
        raise HTTPException(status_code=500, detail="Admin token not configured")

    if provided_token != configured_token:
        raise HTTPException(status_code=401, detail="Invalid admin token")
