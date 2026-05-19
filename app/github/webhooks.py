from json import JSONDecodeError

from fastapi import HTTPException, Request


async def handle_github_webhook(request: Request):
    try:
        payload = await request.json()
    except JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

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
