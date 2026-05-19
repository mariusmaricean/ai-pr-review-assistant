import httpx
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict

from app.config import settings
from app.github.client import GitHubClient


class PullRequestPayload(BaseModel):
    number: int

    model_config = ConfigDict(extra="allow")


class RepositoryPayload(BaseModel):
    full_name: str

    model_config = ConfigDict(extra="allow")


class GitHubWebhookPayload(BaseModel):
    action: str | None = None
    pull_request: PullRequestPayload | None = None
    repository: RepositoryPayload | None = None

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "example": {
                "action": "opened",
                "pull_request": {
                    "number": 1,
                },
                "repository": {
                    "full_name": "owner/repo",
                },
            }
        },
    )


async def handle_github_webhook(payload: GitHubWebhookPayload):
    action = payload.action
    pull_request = payload.pull_request
    repository = payload.repository

    if pull_request is None or repository is None:
        return {"status": "ignored", "reason": "not a pull request event"}

    pr_number = pull_request.number
    repo_name = repository.full_name

    github_client = GitHubClient(settings.github_token)

    try:
        files = await github_client.get_pull_request_files(
            repo_full_name=repo_name,
            pr_number=pr_number,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=_github_error_detail(
                status_code=exc.response.status_code,
                repo_name=repo_name,
                pr_number=pr_number,
            ),
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="GitHub API is unreachable") from exc

    return {
        "status": "received",
        "action": action,
        "repository": repo_name,
        "pull_request": pr_number,
        "changed_files": len(files),
        "files": [
            {
                "filename": file["filename"],
                "status": file["status"],
            }
            for file in files
        ],
    }


def _github_error_detail(status_code: int, repo_name: str, pr_number: int):
    if status_code == 401:
        return "GitHub token is invalid or missing"
    if status_code == 403:
        return "GitHub token does not have access to this repository"
    if status_code == 404:
        return {
            "message": "GitHub repository or pull request not found",
            "repository": repo_name,
            "pull_request": pr_number,
            "hint": "Use repository.full_name as 'owner/repo' and make sure the PR number exists. For private repos, the token needs access to the repo.",
        }

    return "GitHub API request failed"
