# app/main.py

from fastapi import FastAPI, Request  # type: ignore[import]

app = FastAPI(title="AI PR Review Assistant")


@app.post("/webhooks/github")
async def github_webhook(request: Request):
    payload = await request.json()

    action = payload.get("action")
    pull_request = payload.get("pull_request")
    repository = payload.get("repository")

    if not pull_request or not repository:
        return {"status": "ignored", "reason": "not a pull request event"}

    pr_number = pull_request.get("number")
    repo_name = repository.get("full_name")

    return {
        "status": "received",
        "action": action,
        "repository": repo_name,
        "pull_request": pr_number,
    }