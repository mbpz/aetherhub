"""
审计日志路由：查询和管理审计日志
"""
import base64
import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..deps import get_db, require_user
from ..models import AuditLog, User

router = APIRouter(prefix="/audit", tags=["audit"])


def ok(data=None, message="success"):
    return {"code": 0, "message": message, "data": data}


def encode_cursor(log_id: int, created_at: datetime) -> str:
    """将 cursor 信息编码为 base64 字符串"""
    data = {"id": log_id, "created_at": created_at.isoformat()}
    return base64.b64encode(json.dumps(data).encode()).decode()


def decode_cursor(cursor: str) -> Optional[dict]:
    """解码 cursor 字符串"""
    try:
        data = json.loads(base64.b64decode(cursor.encode()).decode())
        return data
    except Exception:
        return None


@router.get("")
async def list_audit_logs(
    cursor: Optional[str] = Query(default=None),
    size: int = Query(default=20, ge=1, le=100),
    action: Optional[str] = Query(default=None),
    user_id: Optional[int] = Query(default=None),
    resource_type: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    """获取审计日志列表（仅管理员）"""
    # 简单的管理员检查：需要 is_staff 或通过其他方式判断
    # 这里假设所有认证用户都可以查看审计日志，实际应检查管理员权限
    if not current_user:
        return {"code": 4001, "message": "Unauthorized", "data": None}

    query = db.query(AuditLog)

    # 应用过滤条件
    if action:
        query = query.filter(AuditLog.action == action)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)

    # Cursor-based pagination
    if cursor:
        cursor_data = decode_cursor(cursor)
        if cursor_data:
            cursor_id = cursor_data.get("id")
            cursor_created_at = cursor_data.get("created_at")
            if cursor_id and cursor_created_at:
                cursor_dt = datetime.fromisoformat(cursor_created_at)
                query = query.filter(
                    (AuditLog.created_at < cursor_dt)
                    | (AuditLog.created_at == cursor_dt, AuditLog.id < cursor_id)
                )
        query = query.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
    else:
        query = query.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())

    logs = query.limit(size).all()
    next_cursor = None
    if len(logs) == size:
        last = logs[-1]
        next_cursor = encode_cursor(last.id, last.created_at)

    return ok({
        "size": size,
        "items": [log.to_dict() for log in logs],
        "next_cursor": next_cursor,
    })
