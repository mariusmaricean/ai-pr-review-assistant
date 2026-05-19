# app/main.py

from fastapi import Depends, FastAPI

from app.config import settings
from app.github.validators import validate_github_event
from app.github.webhooks import GitHubWebhookPayload, handle_github_webhook


app = FastAPI(
    title=settings.app_name,
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
)


@app.post("/webhooks/github")
async def github_webhook(
    payload: GitHubWebhookPayload,
    github_event: str = Depends(validate_github_event),
):
    return await handle_github_webhook(payload)
