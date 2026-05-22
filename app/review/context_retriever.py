from app.github.client import GitHubClient


DEFAULT_CONTEXT_FILES = [
    "README.md",
    "CONTRIBUTING.md",
    "docs/architecture.md",
]


async def load_repository_context(
    github_client: GitHubClient,
    repo_full_name: str,
    ref: str | None,
) -> str:
    sections = []

    for path in DEFAULT_CONTEXT_FILES:
        content = await github_client.get_file_content(
            repo_full_name=repo_full_name,
            path=path,
            ref=ref,
        )

        if content:
            sections.append(
                f"""
Context File: {path}

{content[:4000]}
"""
            )

    return "\n---\n".join(sections)
