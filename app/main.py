# app/main.py

from fastapi import Depends, FastAPI, Request

from app.config import settings
from app.core.logging import configure_logging
from app.github.signature import verify_github_signature
from app.github.validators import validate_github_event
from app.github.webhooks import handle_github_webhook
from app.retrieval.routes import router as retrieval_router


configure_logging()

app = FastAPI(title=settings.app_name)
app.include_router(retrieval_router)


@app.post("/webhooks/github")
async def github_webhook(
    request: Request,
    github_event: str = Depends(validate_github_event),
    body: bytes = Depends(verify_github_signature),
):
    return await handle_github_webhook(request, body)
