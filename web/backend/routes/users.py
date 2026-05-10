"""
User routes: profile, stats, preferences
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional, List

from ..deps import get_db, require_user
from ..models import User, Skill, SkillStar

router = APIRouter(prefix="/users", tags=["users"])

def ok(data=None, message="success"):
    return {"code": 0, "message": message, "data": data}

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None

@router.get("/me")
async def get_my_profile(current_user: User = Depends(require_user)):
    """Get current user profile"""
    return ok(current_user.to_dict())

@router.put("/me")
async def update_my_profile(
    update: UserProfileUpdate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Update current user profile"""
    if update.name is not None:
        current_user.name = update.name
    if update.bio is not None:
        current_user.bio = update.bio
    db.commit()
    return ok(current_user.to_dict(), "Profile updated")

@router.get("/me/stats")
async def get_my_stats(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Get current user stats (skills created, stars received, etc)"""
    skills_count = db.query(Skill).filter(Skill.author_id == current_user.id).count()
    stars_received = db.query(Skill).filter(Skill.author_id == current_user.id).with_entities(func.sum(Skill.star_count)).scalar() or 0
    stars_given = db.query(SkillStar).filter(SkillStar.user_id == current_user.id).count()

    return ok({
        "skills_count": skills_count,
        "stars_received": stars_received,
        "stars_given": stars_given,
    })

@router.get("/{user_id}")
async def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    """Get any user public profile"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"code": 4004, "message": "User not found", "data": None}
    # Only return public info
    return ok({
        "id": user.id,
        "login": user.login,
        "name": user.name,
        "avatar_url": user.avatar_url,
        "bio": user.bio,
        "html_url": user.html_url,
    })

@router.get("/{user_id}/skills")
async def get_user_skills(user_id: int, db: Session = Depends(get_db)):
    """Get public skills by a user"""
    skills = db.query(Skill).filter(
        Skill.author_id == user_id,
        Skill.is_public == True
    ).all()
    return ok([s.to_dict(include_author=False) for s in skills])