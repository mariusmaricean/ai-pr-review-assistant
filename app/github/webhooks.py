from pydantic import BaseModel, ConfigDict

from app.tasks import review_pull_request


class PullRequestHeadPayload(BaseModel):
    ref: str | None = None
    sha: str | None = None

    model_config = ConfigDict(extra="allow")


class PullRequestPayload(BaseModel):
    number: int
    head: PullRequestHeadPayload | None = None

    model_config = ConfigDict(extra="allow")


class RepositoryPayload(BaseModel):
    full_name: str

    model_config = ConfigDict(extra="allow")


class InstallationPayload(BaseModel):
    id: int

    model_config = ConfigDict(extra="allow")


class GitHubWebhookPayload(BaseModel):
    action: str | None = None
    pull_request: PullRequestPayload | None = None
    repository: RepositoryPayload | None = None
    installation: InstallationPayload | None = None

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "example": {
                "action": "opened",
                "pull_request": {
                    "number": 1,
                    "head": {
                        "ref": "feature-branch",
                        "sha": "abc123",
                    },
                },
                "repository": {
                    "full_name": "owner/repo",
                },
                "installation": {"id": 123456},
            }
        },
    )


async def handle_github_webhook(payload: GitHubWebhookPayload):
    pull_request = payload.pull_request
    repository = payload.repository

    if pull_request is None or repository is None:
        return {"status": "ignored", "reason": "not a pull request event"}

    job = review_pull_request.delay(
        payload.model_dump(mode="json", exclude_none=True)
    )

    return {
        "status": "queued",
        "job_id": job.id,
        "action": payload.action,
        "repository": repository.full_name,
        "pull_request": pull_request.number,
    }
