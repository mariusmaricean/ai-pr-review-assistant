import logging
import time

import httpx

from app.config import settings
from app.core.telemetry import tracer
from app.github.app_auth import get_installation_token
from app.github.client import GitHubClient
from app.review.config_loader import (
    filter_ignored_files,
    load_review_config_from_text,
)
from app.review.context_retriever import load_repository_context
from app.review.idempotency import acquire_review_lock, mark_review_completed
from app.review.line_filter import filter_findings_to_valid_lines
from app.review.orchestrator import run_review


logger = logging.getLogger(__name__)


async def process_pull_request_review(payload: dict) -> dict:
    start_time = time.perf_counter()

    pull_request = payload["pull_request"]
    repository = payload["repository"]
    installation_id = payload.get("installation", {}).get("id")

    pr_number = pull_request["number"]
    repo_name = repository["full_name"]
    branch_name = pull_request.get("head", {}).get("ref")
    commit_sha = pull_request.get("head", {}).get("sha")
    review_job_id = payload.get("_review_job_id")

    with tracer.start_as_current_span("process_pull_request_review") as span:
        span.set_attribute("repository", repo_name)
        span.set_attribute("pull_request", pr_number)
        span.set_attribute("commit_sha", commit_sha or "")
        span.set_attribute("review_job_id", review_job_id or "")

        if not acquire_review_lock(repo_name, pr_number, commit_sha, review_job_id):
            span.set_attribute("review.skipped", True)
            span.set_attribute("review.skip_reason", "duplicate_review_job")

            logger.info(
                "Skipping duplicate PR review repository=%s pull_request=%s commit_sha=%s",
                repo_name,
                pr_number,
                commit_sha,
                extra={
                    "repository": repo_name,
                    "pull_request": pr_number,
                    "commit_sha": commit_sha,
                    "review_job_id": review_job_id,
                },
            )

            return {
                "status": "skipped",
                "reason": "duplicate_review_job",
                "repository": repo_name,
                "pull_request": pr_number,
                "commit_sha": commit_sha,
                "review_job_id": review_job_id,
            }

        logger.info(
            "Starting PR review repository=%s pull_request=%s",
            repo_name,
            pr_number,
            extra={
                "repository": repo_name,
                "pull_request": pr_number,
                "commit_sha": commit_sha,
                "review_job_id": review_job_id,
            },
        )

        github_token = settings.github_token

        if installation_id:
            span.set_attribute("github.installation_id", installation_id)

            logger.info(
                "Using GitHub App installation token repository=%s pull_request=%s installation_id=%s",
                repo_name,
                pr_number,
                installation_id,
                extra={
                    "repository": repo_name,
                    "pull_request": pr_number,
                    "installation_id": installation_id,
                },
            )

            with tracer.start_as_current_span("github_installation_token"):
                github_token = await get_installation_token(installation_id)

        github_client = GitHubClient(github_token)

        with tracer.start_as_current_span("load_review_config") as config_span:
            config_text = await github_client.get_file_content(
                repo_full_name=repo_name,
                path=".ai-pr-review.yml",
                ref=branch_name,
            )

            review_config = load_review_config_from_text(config_text)

            config_span.set_attribute("config_present", config_text is not None)
            config_span.set_attribute("min_confidence", review_config.min_confidence)
            config_span.set_attribute("max_comments", review_config.max_comments)
            config_span.set_attribute("ignored_paths", len(review_config.ignored_paths))

        logger.info(
            "Loaded review config repository=%s pull_request=%s config_present=%s min_confidence=%s max_comments=%s ignored_paths=%s",
            repo_name,
            pr_number,
            config_text is not None,
            review_config.min_confidence,
            review_config.max_comments,
            len(review_config.ignored_paths),
            extra={
                "repository": repo_name,
                "pull_request": pr_number,
                "config_present": config_text is not None,
                "min_confidence": review_config.min_confidence,
                "max_comments": review_config.max_comments,
                "ignored_paths": len(review_config.ignored_paths),
            },
        )

        with tracer.start_as_current_span("fetch_pull_request_files") as files_span:
            files = await github_client.get_pull_request_files(
                repo_full_name=repo_name,
                pr_number=pr_number,
            )

            fetched_files_count = len(files)
            files = filter_ignored_files(files, review_config)

            files_span.set_attribute("fetched_files", fetched_files_count)
            files_span.set_attribute("reviewable_files", len(files))

        logger.info(
            "Fetched PR files repository=%s pull_request=%s fetched_files=%s reviewable_files=%s",
            repo_name,
            pr_number,
            fetched_files_count,
            len(files),
            extra={
                "repository": repo_name,
                "pull_request": pr_number,
                "fetched_files": fetched_files_count,
                "reviewable_files": len(files),
            },
        )

        with tracer.start_as_current_span("load_repository_context") as context_span:
            repository_context = await load_repository_context(
                github_client=github_client,
                repo_full_name=repo_name,
                ref=branch_name,
            )
            context_span.set_attribute("repository_context_length", len(repository_context))

        logger.info(
            "Loaded repository context repository=%s pull_request=%s repository_context_length=%s",
            repo_name,
            pr_number,
            len(repository_context),
            extra={
                "repository": repo_name,
                "pull_request": pr_number,
                "repository_context_length": len(repository_context),
            },
        )

        with tracer.start_as_current_span("run_ai_review_pipeline") as review_span:
            review_span.set_attribute("repository_context_length", len(repository_context))
            review = await run_review(files, repository_context)
            review_span.set_attribute("raw_findings", len(review.findings))

        logger.info(
            "Generated AI review repository=%s pull_request=%s raw_findings=%s",
            repo_name,
            pr_number,
            len(review.findings),
            extra={
                "repository": repo_name,
                "pull_request": pr_number,
                "raw_findings": len(review.findings),
            },
        )

        with tracer.start_as_current_span("filter_review_findings") as filter_span:
            confidence_filtered_findings = [
                finding
                for finding in review.findings
                if finding.confidence >= review_config.min_confidence
            ]

            filtered_findings = filter_findings_to_valid_lines(
                confidence_filtered_findings,
                files,
            )

            filtered_findings = filtered_findings[: review_config.max_comments]

            filter_span.set_attribute("confidence_findings", len(confidence_filtered_findings))
            filter_span.set_attribute("valid_line_findings", len(filtered_findings))

        logger.info(
            "Filtered findings repository=%s pull_request=%s confidence_findings=%s valid_line_findings=%s",
            repo_name,
            pr_number,
            len(confidence_filtered_findings),
            len(filtered_findings),
            extra={
                "repository": repo_name,
                "pull_request": pr_number,
                "confidence_findings": len(confidence_filtered_findings),
                "valid_line_findings": len(filtered_findings),
            },
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

        with tracer.start_as_current_span("publish_github_review") as publish_span:
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

                publish_span.set_attribute("published_as", published_as)
                publish_span.set_attribute("comments", len(inline_comments))

                logger.info(
                    "Published GitHub review repository=%s pull_request=%s published_as=%s comments=%s",
                    repo_name,
                    pr_number,
                    published_as,
                    len(inline_comments),
                    extra={
                        "repository": repo_name,
                        "pull_request": pr_number,
                        "published_as": published_as,
                        "comments": len(inline_comments),
                    },
                )

            except httpx.HTTPStatusError as error:
                publish_span.set_attribute("github_publish_failed", True)
                publish_span.set_attribute("status_code", error.response.status_code)

                logger.warning(
                    "Inline GitHub review failed; posting fallback repository=%s pull_request=%s status_code=%s",
                    repo_name,
                    pr_number,
                    error.response.status_code,
                    extra={
                        "repository": repo_name,
                        "pull_request": pr_number,
                        "status_code": error.response.status_code,
                    },
                )

                await github_client.post_pull_request_comment(
                    repo_full_name=repo_name,
                    pr_number=pr_number,
                    body=f"{review_body}\n\nInline review failed, posted fallback summary.",
                )
                published_as = "fallback_summary_comment"

                publish_span.set_attribute("published_as", published_as)

                logger.info(
                    "Published GitHub fallback review repository=%s pull_request=%s",
                    repo_name,
                    pr_number,
                    extra={
                        "repository": repo_name,
                        "pull_request": pr_number,
                        "published_as": published_as,
                    },
                )

        mark_review_completed(repo_name, pr_number, commit_sha)

        duration = time.perf_counter() - start_time

        span.set_attribute("duration_seconds", round(duration, 2))
        span.set_attribute("findings", len(filtered_findings))
        span.set_attribute("published_as", published_as)

        logger.info(
            "Completed PR review repository=%s pull_request=%s duration_seconds=%s findings=%s published_as=%s",
            repo_name,
            pr_number,
            round(duration, 2),
            len(filtered_findings),
            published_as,
            extra={
                "repository": repo_name,
                "pull_request": pr_number,
                "duration_seconds": round(duration, 2),
                "findings": len(filtered_findings),
                "published_as": published_as,
                "commit_sha": commit_sha,
            },
        )

        return {
            "status": "completed",
            "repository": repo_name,
            "pull_request": pr_number,
            "commit_sha": commit_sha,
            "changed_files": len(files),
            "findings": len(filtered_findings),
            "published_as": published_as,
            "duration_seconds": round(duration, 2),
        }
