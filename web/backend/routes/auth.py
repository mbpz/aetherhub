"""
认证路由：GitHub OAuth + JWT
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Optional

from ..deps import get_db, get_optional_user, require_user
from ..models import User
from ..auth import (
    generate_oauth_url, validate_state,
    exchange_code_for_token, get_github_user,
    create_jwt, is_mock_mode
)

router = APIRouter(prefix="/auth", tags=["auth"])

FRONTEND_URL = "http://localhost:5173"


def ok(data=None, message="success"):
    return {"code": 0, "message": message, "data": data}


def err(code: int, message: str):
    return JSONResponse(
        status_code=400,
        content={"code": code, "message": message, "data": None},
    )


@router.get("/login")
async def login():
    """获取 GitHub OAuth 授权 URL"""
    url, state = generate_oauth_url()
    return ok({"auth_url": url, "mock_mode": is_mock_mode()})


@router.get("/callback")
async def callback(
    code: Optional[str] = Query(default=None),
    state: Optional[str] = Query(default=None),
    error: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """GitHub OAuth 回调"""
    # 用户取消授权
    if error:
        return RedirectResponse(
            url=f"{FRONTEND_URL}/auth/callback?error={error}"
        )

    # 验证 state（CSRF 防护）
    if not state or not validate_state(state):
        return RedirectResponse(
            url=f"{FRONTEND_URL}/auth/callback?error=invalid_state"
        )

    if not code:
        return RedirectResponse(
            url=f"{FRONTEND_URL}/auth/callback?error=no_code"
        )

    # 换取 access_token
    access_token = await exchange_code_for_token(code)
    if not access_token:
        return RedirectResponse(
            url=f"{FRONTEND_URL}/auth/callback?error=token_exchange_failed"
        )

    # 获取 GitHub 用户信息
    github_user = await get_github_user(access_token)
    if not github_user:
        return RedirectResponse(
            url=f"{FRONTEND_URL}/auth/callback?error=user_fetch_failed"
        )

    # 创建或更新用户
    user = db.query(User).filter(User.github_id == github_user["id"]).first()
    if user:
        user.login = github_user.get("login", user.login)
        user.name = github_user.get("name", user.name)
        user.avatar_url = github_user.get("avatar_url", user.avatar_url)
        user.email = github_user.get("email", user.email)
        user.bio = github_user.get("bio", user.bio)
        user.html_url = github_user.get("html_url", user.html_url)
    else:
        user = User(
            github_id=github_user["id"],
            login=github_user.get("login", ""),
            name=github_user.get("name"),
            avatar_url=github_user.get("avatar_url"),
            email=github_user.get("email"),
            bio=github_user.get("bio"),
            html_url=github_user.get("html_url"),
        )
        db.add(user)

    db.commit()
    db.refresh(user)

    # 生成 JWT
    token = create_jwt(user.id)

    # 重定向到前端，携带 token
    return RedirectResponse(
        url=f"{FRONTEND_URL}/auth/callback?token={token}"
    )


@router.get("/mock-callback")
async def mock_callback(
    state: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """Mock 模式回调（无需真实 GitHub OAuth）"""
    if not state or not validate_state(state):
        return RedirectResponse(
            url=f"{FRONTEND_URL}/auth/callback?error=invalid_state"
        )

    # 创建 mock 用户
    mock_github_id = 99999999
    user = db.query(User).filter(User.github_id == mock_github_id).first()
    if not user:
        user = User(
            github_id=mock_github_id,
            login="demo-user",
            name="Demo User",
            avatar_url="https://avatars.githubusercontent.com/u/583231",
            bio="AetherHub Demo User",
            html_url="https://github.com/octocat",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_jwt(user.id)
    return RedirectResponse(
        url=f"{FRONTEND_URL}/auth/callback?token={token}"
    )


@router.get("/me")
async def me(current_user: User = Depends(require_user)):
    """获取当前登录用户信息"""
    return ok(current_user.to_dict())


@router.post("/logout")
async def logout(current_user: User = Depends(require_user)):
    """登出（前端清除 token，后端无状态）"""
    return ok(None, "Logged out successfully")
