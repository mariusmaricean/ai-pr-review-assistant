import asyncio
import logging

from app.ai.client import generate_pr_review
from app.core.telemetry import tracer
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

    with tracer.start_as_current_span("review_chunk_execution") as span:
        span.set_attribute("reviewer_type", reviewer_type)
        span.set_attribute("language", language)
        span.set_attribute("files", len(chunk))
        span.set_attribute("context_length", len(context))

        logger.info(
            "Running reviewer chunk reviewer_type=%s language=%s files=%s",
            reviewer_type,
            language,
            len(chunk),
            extra={
                "reviewer_type": reviewer_type,
                "language": language,
                "files": len(chunk),
                "context_length": len(context),
            },
        )

        return await generate_pr_review(
            review_context=context,
            language=language,
            reviewer_type=reviewer_type,
        )


async def run_review(files: list[dict]) -> ReviewResult:
    chunks = chunk_files(files)

    with tracer.start_as_current_span("review_pipeline_execution") as span:
        span.set_attribute("chunks", len(chunks))
        span.set_attribute("files", len(files))
        span.set_attribute("reviewers", len(REVIEWER_TYPES))

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

        span.set_attribute("reviewer_tasks", len(tasks))

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

        span.set_attribute("review_results", len(results))
        span.set_attribute("findings", len(findings))

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
