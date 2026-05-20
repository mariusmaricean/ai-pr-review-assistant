from openai import AsyncOpenAI

from app.config import settings


client = AsyncOpenAI(api_key=settings.openai_api_key)


async def generate_pr_review(review_context: str) -> str:
    prompt = f"""
You are a senior software engineer reviewing a pull request.

Review the following code changes.

Focus on:
- bugs
- security issues
- performance concerns
- maintainability
- missing tests
- architecture concerns

Provide:
1. Summary
2. Key findings
3. Suggested improvements

PR Diff:
{review_context}
"""

    response = await client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "You are an expert code reviewer.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content or ""
