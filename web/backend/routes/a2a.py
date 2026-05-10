"""
A2A Protocol Routes - Agent-to-Agent Communication
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..deps import get_db
from ..models import Skill

router = APIRouter(prefix="/a2a", tags=["a2a"])


class SkillRequest(BaseModel):
    """A2A skill request payload"""
    capability: str  # e.g., "csv-processing", "text-summarization"
    params: Optional[dict] = None
    preferred_category: Optional[str] = None


class SkillResponse(BaseModel):
    """A2A skill response"""
    skill_id: int
    skill_name: str
    version: str
    description: str
    category: str
    tags: list
    how_to_execute: str  # Instructions for the agent


@router.post("/skill-request")
async def request_skill(
    request: SkillRequest,
    db: Session = Depends(get_db),
):
    """
    A2A Skill Request Endpoint

    Agents can request a skill capability and receive:
    - Skill metadata
    - How to execute the skill

    This is a simple A2A protocol for agent-to-agent communication.
    """
    # Search for skills matching the capability
    query = db.query(Skill).filter(Skill.is_public == True)

    # Try to match by name, description, or tags
    capability = request.capability.lower()
    query = query.filter(
        Skill.name.ilike(f"%{capability}%") |
        Skill.description.ilike(f"%{capability}%") |
        Skill.tags.ilike(f"%{capability}%")
    )

    if request.preferred_category:
        query = query.filter(Skill.category == request.preferred_category)

    # Get the highest-rated matching skill
    skill = query.order_by(
        (Skill.star_count * 3 + Skill.download_count * 2).desc()
    ).first()

    if not skill:
        return {
            "code": 4040,
            "message": f"No skill found for capability: {request.capability}",
            "data": None,
        }

    # Build execution instructions
    how_to_execute = f"""
Skill: {skill.name} v{skill.version}
Category: {skill.category}

Description:
{skill.description}

Files available: {[f.filename for f in skill.files]}

To execute this skill:
1. Download or access the skill files from the marketplace
2. Review the skill.py file for the main class/method
3. Invoke the skill with appropriate parameters

Example usage:
```python
from skill import {skill.name.split('-')[0].title().replace('-', '')}Client
client = {skill.name.split('-')[0].title().replace('-', '')}Client()
result = client.execute(**{request.params or {}})
```

For more details, see the skill's README or SKILL.md documentation.
""".strip()

    return {
        "code": 0,
        "message": "Skill found",
        "data": {
            "skill_id": skill.id,
            "skill_name": skill.name,
            "version": skill.version,
            "description": skill.description,
            "category": skill.category,
            "tags": skill.get_tags(),
            "star_count": skill.star_count,
            "download_count": skill.download_count,
            "average_rating": skill.average_rating,
            "how_to_execute": how_to_execute,
            "author": {
                "login": skill.author.login,
                "avatar_url": skill.author.avatar_url,
            } if skill.author else None,
        },
    }


@router.get("/capabilities")
async def list_capabilities(
    db: Session = Depends(get_db),
):
    """
    List all unique capabilities (categories + tags) available in the marketplace.
    Useful for agents to discover what skills are available.
    """
    from ..models import Skill

    # Get all unique categories
    categories = db.query(Skill.category).filter(
        Skill.is_public == True,
        Skill.category != None,
    ).distinct().all()
    categories = [c[0] for c in categories if c[0]]

    # Get all unique tags
    all_tags = set()
    skills_with_tags = db.query(Skill.tags).filter(
        Skill.is_public == True,
        Skill.tags != None,
    ).all()
    for tags_str in skills_with_tags:
        try:
            import json
            tags = json.loads(tags_str[0])
            all_tags.update(tags)
        except Exception:
            pass

    return {
        "code": 0,
        "message": "success",
        "data": {
            "categories": categories,
            "tags": sorted(list(all_tags)),
        },
    }
