import httpx
from fastapi import HTTPException
from openai import OpenAIError
from pydantic import BaseModel, ConfigDict

from app.config import settings
from app.github.client import GitHubClient
from app.review.line_filter import filter_findings_to_valid_lines
from app.review.orchestrator import run_review


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
                operation="fetch_files",
            ),
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="GitHub API is unreachable") from exc

    try:
        review = await run_review(files)
    except (OpenAIError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail="OpenAI review generation failed",
        ) from exc

    confidence_filtered_findings = [
        finding
        for finding in review.findings
        if finding.confidence >= 0.7
    ]

    filtered_findings = filter_findings_to_valid_lines(
        confidence_filtered_findings,
        files,
    )

    inline_comments = [
        {
            "path": finding.file,
            "line": finding.line,
            "body": f"**{finding.title}**\n\n{finding.comment}\n\nSeverity: `{finding.severity}`",
        }
        for finding in filtered_findings
    ]

    review_body = f"""
## AI PR Review Assistant

{review.summary}

Findings: {len(filtered_findings)}
"""

    try:
        if inline_comments:
            await github_client.create_pull_request_review(
                repo_full_name=repo_name,
                pr_number=pr_number,
                body=review_body,
                comments=inline_comments,
            )
            published_as = "inline_review"
        else:
            await github_client.post_pull_request_comment(
                repo_full_name=repo_name,
                pr_number=pr_number,
                body=f"{review_body}\n\nNo high-confidence inline findings.",
            )
            published_as = "summary_comment"

    except httpx.HTTPStatusError:
        fallback_body = f"""
## AI PR Review Assistant

{review.summary}

Inline review failed, so here are the findings as a summary:

"""

        for finding in filtered_findings:
            fallback_body += f"""
- [{finding.severity.upper()}] `{finding.file}` line {finding.line}
  - {finding.title}
  - {finding.comment}
"""

        await github_client.post_pull_request_comment(
            repo_full_name=repo_name,
            pr_number=pr_number,
            body=fallback_body,
        )

        published_as = "fallback_summary_comment"
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="GitHub API is unreachable") from exc

    return {
        "status": "completed",
        "repository": repo_name,
        "pull_request": pr_number,
        "changed_files": len(files),
        "findings": len(filtered_findings),
        "published_as": published_as,
    }


def _github_error_detail(
    status_code: int,
    repo_name: str,
    pr_number: int,
    operation: str,
):
    if status_code == 401:
        return "GitHub token is invalid or missing"
    if status_code == 403:
        if operation == "post_comment":
            return (
                "GitHub token cannot post PR comments. For fine-grained tokens, "
                "grant Issues read/write permission on this repository."
            )
        if operation == "post_review":
            return (
                "GitHub token cannot create pull request reviews. For fine-grained "
                "tokens, grant Pull requests read/write permission on this repository."
            )
        if operation == "fetch_files":
            return (
                "GitHub token cannot read pull request files. Make sure the token "
                "has access to this repository and Pull requests read permission."
            )

        return "GitHub token does not have access to this repository"
    if status_code == 404:
        return {
            "message": "GitHub repository or pull request not found",
            "repository": repo_name,
            "pull_request": pr_number,
            "hint": "Use repository.full_name as owner/repo and make sure the PR number exists. For private repos, the token needs access to the repo.",
        }

    return "GitHub API request failed"
