"""
GitHub OAuth 认证模块
"""
import os
import secrets
import httpx
import jwt as pyjwt
from datetime import datetime, timedelta, timezone
from typing import Optional

# ─── 环境变量读取 ──────────────────────────────────────────────────────────────
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_CALLBACK_URL = os.getenv(
    "GITHUB_CALLBACK_URL", "http://localhost:8000/api/v1/auth/callback"
)

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "aetherhub-dev-secret-change-in-prod")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))

# In-memory CSRF state store (production should use Redis/DB)
_oauth_states: dict[str, datetime] = {}


def generate_oauth_url() -> tuple[str, str]:
    """生成 GitHub OAuth 授权 URL，返回 (url, state)"""
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = datetime.now(timezone.utc)
    # Clean up old states (>10 minutes)
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=10)
    expired = [k for k, v in _oauth_states.items() if v < cutoff]
    for k in expired:
        del _oauth_states[k]

    scope = "read:user,user:email"
    url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&scope={scope}"
        f"&state={state}"
        f"&redirect_uri={GITHUB_CALLBACK_URL}"
    )
    return url, state


def validate_state(state: str) -> bool:
    """验证 OAuth state，防 CSRF"""
    if state not in _oauth_states:
        return False
    created = _oauth_states.pop(state)
    age = datetime.now(timezone.utc) - created
    return age < timedelta(minutes=10)


async def exchange_code_for_token(code: str) -> Optional[str]:
    """用 code 换取 GitHub access_token"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"},
            timeout=15,
        )
        data = resp.json()
        return data.get("access_token")


async def get_github_user(access_token: str) -> Optional[dict]:
    """用 access_token 获取 GitHub 用户信息"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"token {access_token}",
                "Accept": "application/vnd.github.v3+json",
            },
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json()
        return None


def create_jwt(user_id: int) -> str:
    """生成 JWT Token"""
    payload = {
        "sub": str(user_id),
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS),
    }
    return pyjwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_jwt(token: str) -> Optional[dict]:
    """解码 JWT Token，返回 payload 或 None"""
    try:
        payload = pyjwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except pyjwt.ExpiredSignatureError:
        return None
    except pyjwt.InvalidTokenError:
        return None
