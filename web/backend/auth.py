"""
GitHub OAuth 认证模块 & JWT 工具
"""
import os
import secrets
import httpx
import jwt as pyjwt
from datetime import datetime, timedelta, timezone
from typing import Optional

# ─── 环境变量配置 ─────────────────────────────────────────────────────────────
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_CALLBACK_URL = os.getenv(
    "GITHUB_CALLBACK_URL", "http://localhost:8000/api/v1/auth/callback"
)

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "aetherhub-dev-secret-change-in-prod")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))

# Mock 模式标志
MOCK_MODE = not (GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET)

# In-memory CSRF state store（生产环境应用 Redis）
_oauth_states: dict[str, datetime] = {}


def is_mock_mode() -> bool:
    return MOCK_MODE


def generate_oauth_url() -> tuple[str, str]:
    """生成 GitHub OAuth 授权 URL，返回 (url, state)"""
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = datetime.now(timezone.utc)
    # 清理超时 state
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=10)
    expired = [k for k, v in _oauth_states.items() if v < cutoff]
    for k in expired:
        del _oauth_states[k]

    if MOCK_MODE:
        url = f"http://localhost:8000/api/v1/auth/mock-callback?state={state}"
    else:
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
    if not state or state not in _oauth_states:
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


def create_refresh_token(user_id: int) -> str:
    """生成 JWT 刷新令牌（有效期 30 天）"""
    payload = {
        "sub": str(user_id),
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(days=30),
        "type": "refresh",
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


def decode_jwt_allow_expired(token: str) -> Optional[dict]:
    """解码 JWT Token（允许过期），用于 refresh 流程"""
    try:
        payload = pyjwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={"verify_exp": False}
        )
        return payload
    except pyjwt.InvalidTokenError:
        return None


def verify_refresh_token(token: str) -> Optional[int]:
    """
    验证刷新令牌，返回 user_id 或 None

    刷新令牌有效期 30 天，仅限使用一次（使用后作废）
    """
    payload = decode_jwt_allow_expired(token)
    if payload is None:
        return None

    # 检查是否是刷新令牌
    if payload.get("type") != "refresh":
        return None

    # 检查是否已过期（30 天）
    exp = payload.get("exp")
    if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
        return None

    user_id = payload.get("sub")
    return int(user_id) if user_id else None


# 刷新令牌黑名单（已使用的令牌）
_refresh_token_blacklist = set()


def invalidate_refresh_token(token: str):
    """将刷新令牌加入黑名单（一次性使用）"""
    _refresh_token_blacklist.add(token)


def is_refresh_token_valid(token: str) -> bool:
    """检查刷新令牌是否有效（未使用且未过期）"""
    if token in _refresh_token_blacklist:
        return False

    payload = decode_jwt_allow_expired(token)
    if payload is None:
        return False

    if payload.get("type") != "refresh":
        return False

    exp = payload.get("exp")
    if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
        return False

    return True
