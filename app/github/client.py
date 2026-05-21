import base64

import httpx


class GitHubClient:
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.github.com"

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def get_pull_request_files(self, repo_full_name: str, pr_number: int):
        repo_full_name = self._normalize_repo_full_name(repo_full_name)
        url = f"{self.base_url}/repos/{repo_full_name}/pulls/{pr_number}/files"

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, headers=self._headers())
            response.raise_for_status()
            return response.json()

    async def get_file_content(
        self,
        repo_full_name: str,
        path: str,
        ref: str | None = None,
    ) -> str | None:
        repo_full_name = self._normalize_repo_full_name(repo_full_name)
        url = f"{self.base_url}/repos/{repo_full_name}/contents/{path}"
        params = {"ref": ref} if ref else None

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                url,
                headers=self._headers(),
                params=params,
            )

            if response.status_code == 404:
                return None

            response.raise_for_status()

            data = response.json()
            encoded_content = data.get("content")

            if not encoded_content:
                return None

            return base64.b64decode(encoded_content).decode("utf-8")

    async def post_pull_request_comment(
        self,
        repo_full_name: str,
        pr_number: int,
        body: str,
    ):
        repo_full_name = self._normalize_repo_full_name(repo_full_name)
        url = f"{self.base_url}/repos/{repo_full_name}/issues/{pr_number}/comments"

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                url,
                headers=self._headers(),
                json={"body": body},
            )
            response.raise_for_status()
            return response.json()

    async def create_pull_request_review(
        self,
        repo_full_name: str,
        pr_number: int,
        body: str,
        comments: list[dict],
    ):
        repo_full_name = self._normalize_repo_full_name(repo_full_name)
        url = f"{self.base_url}/repos/{repo_full_name}/pulls/{pr_number}/reviews"

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                url,
                headers=self._headers(),
                json={
                    "body": body,
                    "event": "COMMENT",
                    "comments": comments,
                },
            )
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
