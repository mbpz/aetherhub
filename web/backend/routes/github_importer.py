"""
GitHub Import 路由：从 GitHub 导入真实 repos 作为技能
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException

from ..services.github_importer import GitHubImporter
from ..deps import get_db, require_user
from ..models import Skill, SkillFile

router = APIRouter(prefix="/github", tags=["github"])

importer = GitHubImporter()


@router.get("/import")
def github_search_import(
    q: str,
    limit: int = 10,
):
    """搜索 GitHub repos 并导入为技能"""
    try:
        repos = importer.search_repos(q, per_page=limit)

        results = []
        for repo in repos:
            results.append({
                "owner": repo.get("owner", {}).get("login"),
                "repo": repo.get("name"),
                "description": repo.get("description"),
                "stars": repo.get("stargazers_count"),
                "url": repo.get("html_url"),
                "language": repo.get("language"),
            })

        return {"repos": results, "total": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/{owner}/{repo}")
def github_import_repo(
    owner: str,
    repo: str,
    db=None,
    current_user=None,
):
    """导入指定 repo 为技能"""
    require_user(current_user)

    try:
        # 获取 repo 详情
        skill_data = importer.import_repo(owner, repo)

        # TODO: 将 repo 保存为 skill 记录
        # 这里需要整合到现有 skill 模型中

        return {
            "status": "imported",
            "owner": owner,
            "repo": repo,
            "skill_id": None,  # 待实现
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))