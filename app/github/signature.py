import hashlib
import hmac

from fastapi import HTTPException, Request

from app.config import settings


async def verify_github_signature(request: Request) -> bytes:
    signature_header = request.headers.get("X-Hub-Signature-256")

    if not signature_header:
        raise HTTPException(status_code=401, detail="Missing GitHub signature")

    if not signature_header.startswith("sha256="):
        raise HTTPException(status_code=401, detail="Invalid signature format")

    body = await request.body()

    expected_signature = "sha256=" + hmac.new(
        settings.github_webhook_secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, signature_header):
        raise HTTPException(status_code=401, detail="Invalid GitHub signature")

    return body
