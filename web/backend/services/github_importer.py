"""
GitHub API 集成：从 GitHub 导入真实 repos 作为技能
"""
import os
import httpx
from typing import List, Dict, Optional

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # 可选，增大 rate limit

class GitHubImporter:
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if GITHUB_TOKEN:
            self.headers["Authorization"] = f"token {GITHUB_TOKEN}"

    def search_repos(self, query: str, per_page: int = 30) -> List[Dict]:
        """搜索 GitHub repos"""
        url = f"{self.base_url}/search/repositories"
        params = {"q": query, "per_page": per_page, "sort": "stars"}

        with httpx.Client() as client:
            resp = client.get(url, params=params, headers=self.headers)
            resp.raise_for_status()
            return resp.json().get("items", [])

    def get_repo_skills(self, owner: str, repo: str) -> Optional[Dict]:
        """获取 repo 的技能信息（从 README 或 SKILL.md）"""
        # Try to find SKILL.md first
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/SKILL.md"
        # Fall back to README for description
        return {"owner": owner, "repo": repo}

    def import_repo(self, owner: str, repo: str) -> Dict:
        """导入单个 repo 为技能"""
        # Implementation
        pass