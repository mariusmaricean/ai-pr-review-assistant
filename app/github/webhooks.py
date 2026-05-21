import json

from fastapi import Request

from app.tasks import review_pull_request


async def handle_github_webhook(request: Request, body: bytes):
    payload = json.loads(body)

    action = payload.get("action")
    pull_request = payload.get("pull_request")
    repository = payload.get("repository")

    if not pull_request or not repository:
        return {"status": "ignored", "reason": "not a pull request event"}

    job = review_pull_request.delay(payload)

    return {
        "status": "queued",
        "job_id": job.id,
        "action": action,
        "repository": repository.get("full_name"),
        "pull_request": pull_request.get("number"),
    }
