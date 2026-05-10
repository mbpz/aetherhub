"""
AetherHub 中间件：Rate Limiting
"""
import time
from typing import Dict, Tuple
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class TokenBucket:
    """Token Bucket Rate Limiter (in-memory)"""

    def __init__(self, rate: int, per_seconds: int):
        self.rate = rate  # tokens per period
        self.per_seconds = per_seconds
        self.tokens: Dict[str, Tuple[int, float]] = {}  # key -> (tokens, last_update)

    def consume(self, key: str) -> bool:
        """尝试消耗一个 token，返回是否成功"""
        now = time.time()
        current_tokens, last_update = self.tokens.get(key, (self.rate, now))

        # 计算时间流逝补充的 tokens
        elapsed = now - last_update
        tokens_to_add = (elapsed / self.per_seconds) * self.rate
        current_tokens = min(self.rate, current_tokens + tokens_to_add)

        if current_tokens >= 1:
            current_tokens -= 1
            self.tokens[key] = (current_tokens, now)
            return True
        else:
            self.tokens[key] = (current_tokens, now)
            return False

    def retry_after(self, key: str) -> int:
        """返回还需要等待多少秒才能获得新 token"""
        now = time.time()
        current_tokens, last_update = self.tokens.get(key, (self.rate, now))
        elapsed = now - last_update
        tokens_to_add = (elapsed / self.per_seconds) * self.rate
        current_tokens = min(self.rate, current_tokens + tokens_to_add)

        if current_tokens >= 1:
            return 0
        tokens_needed = 1 - current_tokens
        return int(tokens_needed * self.per_seconds / self.rate) + 1


# 全局限流器：100 requests/minute for authenticated, 20/min for anonymous
_authenticated_limiter = TokenBucket(rate=100, per_seconds=60)
_anonymous_limiter = TokenBucket(rate=20, per_seconds=60)


def get_client_key(request: Request) -> str:
    """获取客户端标识 key"""
    # 优先使用 X-Forwarded-For 或 X-Real-IP，否则用 client.host
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    if request.client:
        return request.client.host
    return "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """API Rate Limiting Middleware"""

    async def dispatch(self, request: Request, call_next):
        # 跳过非 API 路由
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        # 获取客户端标识
        client_key = get_client_key(request)

        # 检查是否有 Authorization header 来判断是否认证用户
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # 认证用户使用更宽松的限制
            limiter = _authenticated_limiter
        else:
            # 匿名用户使用更严格的限制
            limiter = _anonymous_limiter

        if not limiter.consume(client_key):
            retry_after = limiter.retry_after(client_key)
            return JSONResponse(
                status_code=429,
                content={
                    "code": 4290,
                    "message": "Too Many Requests",
                    "data": {"retry_after": retry_after},
                },
                headers={"Retry-After": str(retry_after)},
            )

        response = await call_next(request)
        return response


def log_audit(
    db,
    user_id: int,
    action: str,
    resource_type: str,
    resource_id: int = None,
    details: dict = None,
    ip_address: str = None,
):
    """记录审计日志（供其他模块调用）"""
    from .models import AuditLog
    import json

    log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=json.dumps(details or {}, ensure_ascii=False),
        ip_address=ip_address,
    )
    db.add(log)
    db.commit()
