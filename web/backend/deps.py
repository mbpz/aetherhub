"""
FastAPI 依赖注入：数据库 Session + 当前用户
"""
from typing import Optional, Generator
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import User
from .auth import decode_jwt


def get_db() -> Generator[Session, None, None]:
    """获取数据库 Session（依赖注入）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_optional_user(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """可选鉴权：有 token 则返回用户，没有则返回 None"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    payload = decode_jwt(token)
    if not payload:
        return None
    user_id = int(payload.get("sub", 0))
    user = db.query(User).filter(User.id == user_id).first()
    return user


def require_user(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    """强制鉴权：未登录则返回 401"""
    user = get_optional_user(authorization, db)
    if not user:
        raise HTTPException(
            status_code=401,
            detail={"code": 4001, "message": "Unauthorized", "data": None},
        )
    return user
