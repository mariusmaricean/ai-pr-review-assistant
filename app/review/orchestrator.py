import asyncio
import logging

from app.ai.client import generate_pr_review
from app.review.chunker import chunk_files
from app.review.context_builder import build_review_context
from app.review.language import detect_language
from app.review.models import ReviewResult
from app.review.reviewer_types import REVIEWER_TYPES


logger = logging.getLogger(__name__)


def detect_chunk_language(chunk: list[dict]) -> str:
    languages = [
        detect_language(file.get("filename", ""))
        for file in chunk
    ]

    non_generic = [language for language in languages if language != "generic"]

    if not non_generic:
        return "generic"

    return max(set(non_generic), key=non_generic.count)


async def review_chunk_with_reviewer(
    chunk: list[dict],
    reviewer_type: str,
):
    context = build_review_context(chunk)
    language = detect_chunk_language(chunk)

    logger.info(
        "Running reviewer chunk reviewer_type=%s language=%s files=%s",
        reviewer_type,
        language,
        len(chunk),
        extra={
            "reviewer_type": reviewer_type,
            "language": language,
            "files": len(chunk),
        },
    )

    return await generate_pr_review(
        review_context=context,
        language=language,
        reviewer_type=reviewer_type,
    )


async def run_review(files: list[dict]) -> ReviewResult:
    chunks = chunk_files(files)

    logger.info(
        "Created review chunks chunks=%s files=%s reviewers=%s",
        len(chunks),
        len(files),
        len(REVIEWER_TYPES),
        extra={
            "chunks": len(chunks),
            "files": len(files),
            "reviewers": len(REVIEWER_TYPES),
        },
    )

    tasks = [
        review_chunk_with_reviewer(chunk, reviewer_type)
        for chunk in chunks
        for reviewer_type in REVIEWER_TYPES
    ]

    logger.info(
        "Executing reviewers tasks=%s",
        len(tasks),
        extra={"reviewer_tasks": len(tasks)},
    )

    results = await asyncio.gather(*tasks)

    summaries = []
    findings = []

    for result in results:
        summaries.append(result.summary)
        findings.extend(result.findings)

    logger.info(
        "Completed reviewers results=%s findings=%s",
        len(results),
        len(findings),
        extra={"review_results": len(results), "findings": len(findings)},
    )

    return ReviewResult(
        summary="\n".join(summaries),
        findings=findings,
    )
