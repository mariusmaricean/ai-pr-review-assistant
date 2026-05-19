# app/main.py

from fastapi import FastAPI

from app.config import settings
from app.github.webhooks import GitHubWebhookPayload, handle_github_webhook

app = FastAPI(title=settings.app_name)


@app.post("/webhooks/github")
async def github_webhook(payload: GitHubWebhookPayload):
    return await handle_github_webhook(payload)
