from fastapi import Header, HTTPException

from app.config import settings


def verify_admin_token(x_admin_token: str | None = Header(default=None)):
    if not settings.admin_api_token:
        raise HTTPException(status_code=500, detail="Admin token not configured")

    if x_admin_token != settings.admin_api_token:
        raise HTTPException(status_code=401, detail="Invalid admin token")
