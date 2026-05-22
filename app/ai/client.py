import json
import logging
import time

from json import JSONDecodeError

from openai import AsyncOpenAI
from pydantic import ValidationError

from app.ai.prompts import (
    REVIEW_SYSTEM_PROMPT,
    REVIEWER_PROFILES,
    build_language_prompt,
)
from app.config import settings
from app.core.telemetry import tracer
from app.review.models import ReviewResult


logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=settings.openai_api_key)


async def generate_pr_review(
    review_context: str,
    language: str,
    reviewer_type: str = "general",
    repository_context: str = "",
) -> ReviewResult:
    reviewer_instructions = REVIEWER_PROFILES.get(reviewer_type, "")
    language_instructions = build_language_prompt(language)

    prompt = f"""
Review this pull request diff.

Reviewer type:
{reviewer_type}

Reviewer instructions:
{reviewer_instructions}

Language/profile:
{language}

Language-specific focus:
{language_instructions}

Repository context:
{repository_context or "No repository context available."}

PR diff:
{review_context}
"""

    with tracer.start_as_current_span("openai_review_generation") as span:
        span.set_attribute("reviewer_type", reviewer_type)
        span.set_attribute("language", language)
        span.set_attribute("prompt_length", len(prompt))
        span.set_attribute("repository_context_length", len(repository_context))

        start = time.perf_counter()

        response = await client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": REVIEW_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.1,
        )

        duration = time.perf_counter() - start
        usage = getattr(response, "usage", None)

        metrics = {
            "reviewer_type": reviewer_type,
            "language": language,
            "duration_seconds": round(duration, 2),
            "prompt_length": len(prompt),
            "repository_context_length": len(repository_context),
        }

        span.set_attribute("duration_seconds", round(duration, 2))

        if usage:
            token_metrics = {
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
            }
            metrics.update(token_metrics)

            for key, value in token_metrics.items():
                if value is not None:
                    span.set_attribute(key, value)

        logger.info(
            "AI review completed reviewer_type=%s language=%s duration_seconds=%s prompt_length=%s",
            reviewer_type,
            language,
            round(duration, 2),
            len(prompt),
            extra=metrics,
        )

    content = response.choices[0].message.content or ""

    try:
        parsed = json.loads(content)
        return ReviewResult(**parsed)

    except (JSONDecodeError, ValidationError) as error:
        logger.warning(
            "Failed to parse AI review response",
            extra={
                "reviewer_type": reviewer_type,
                "language": language,
                "error": str(error),
                "response_preview": content[:500],
            },
        )

        return ReviewResult(
            summary=f"{reviewer_type} reviewer did not return valid structured output.",
            findings=[],
        )
