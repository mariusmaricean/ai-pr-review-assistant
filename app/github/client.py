import httpx


class GitHubClient:
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.github.com"

    async def get_pull_request_files(self, repo_full_name: str, pr_number: int):
        repo_full_name = self._normalize_repo_full_name(repo_full_name)
        url = f"{self.base_url}/repos/{repo_full_name}/pulls/{pr_number}/files"

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()

    def _normalize_repo_full_name(self, repo_full_name: str):
        repo_full_name = repo_full_name.strip()

        if repo_full_name.startswith("https://github.com/"):
            repo_full_name = repo_full_name.removeprefix("https://github.com/")
        elif repo_full_name.startswith("http://github.com/"):
            repo_full_name = repo_full_name.removeprefix("http://github.com/")

        repo_full_name = repo_full_name.removesuffix(".git").strip("/")
        parts = repo_full_name.split("/")

        if len(parts) != 2 or not all(parts) or "://" in repo_full_name:
            raise ValueError("repository.full_name must be in 'owner/repo' format")

        return repo_full_name
