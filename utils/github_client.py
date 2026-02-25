import httpx
import os
import base64
import logging
import asyncio

logger = logging.getLogger("github-client")

class GitHubClient:
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "CodeSight-Reviewer-Bot"
        }

    async def get_diff(self, diff_url: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                diff_url, 
                headers={**self.headers, "Accept": "application/vnd.github.v3.diff"}, 
                follow_redirects=True
            )
            return response.text if response.status_code == 200 else ""

async def get_repo_contents(self, repo_full_name: str, branch: str = "main"):
    url = f"https://api.github.com/repos/{repo_full_name}/git/trees/{branch}?recursive=1"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=self.headers)
        if resp.status_code != 200:
            return []
        
        tree = resp.json().get("tree", [])
        files_to_index = [i["path"] for i in tree if i["path"].endswith(".py") and i["type"] == "blob"]

        async def fetch_file(path):
            file_url = f"https://api.github.com/repos/{repo_full_name}/contents/{path}?ref={branch}"
            f_resp = await client.get(file_url, headers=self.headers)
            if f_resp.status_code == 200:
                data = f_resp.json()
                decoded = base64.b64decode(data["content"]).decode('utf-8')
                return {"path": path, "content": decoded}
            return None

        results = await asyncio.gather(*[fetch_file(path) for path in files_to_index])
        return [r for r in results if r is not None]

    async def post_comment(self, repo_full_name: str, pr_number: int, body: str):
        url = f"https://api.github.com/repos/{repo_full_name}/issues/{pr_number}/comments"
        async with httpx.AsyncClient() as client:
            await client.post(url, headers=self.headers, json={"body": body})