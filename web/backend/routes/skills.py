"""
Skill 路由：CRUD + 搜索 + Star
"""
import base64
import json
import math
import os
import re
import shutil
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse, PlainTextResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, text
import numpy as np

from ..deps import get_db, get_optional_user, require_user
from ..models import Skill, SkillFile, SkillStar, User, SkillVersion, SkillModeration
from ..embeddings import text_to_embedding, cosine_similarity, rrf_fusion, get_embedding
from ..database import engine
from ..middleware import log_audit
from ..services.storage import get_storage

router = APIRouter(prefix="/skills", tags=["skills"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_TOTAL_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml"}

CATEGORIES = ["数据处理", "网络工具", "文件操作", "AI工具", "系统工具", "其他"]


def encode_cursor(skill_id: int, created_at: datetime) -> str:
    """将 cursor 信息编码为 base64 字符串"""
    data = {"id": skill_id, "created_at": created_at.isoformat()}
    return base64.b64encode(json.dumps(data).encode()).decode()


def decode_cursor(cursor: str) -> Optional[dict]:
    """解码 cursor 字符串，返回 dict 或 None"""
    try:
        data = json.loads(base64.b64decode(cursor.encode()).decode())
        return data
    except Exception:
        return None


def ok(data=None, message="success"):
    return {"code": 0, "message": message, "data": data}


def err_response(code: int, message: str, status_code: int = 400):
    return JSONResponse(
        status_code=status_code,
        content={"code": code, "message": message, "data": None},
    )


def safe_filename(filename: str) -> str:
    """安全化文件名，防止路径穿越"""
    filename = os.path.basename(filename)
    filename = re.sub(r"[^\w\.\-]", "_", filename)
    return filename


@router.get("")
async def list_skills(
    q: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    tags: Optional[str] = Query(default=None),
    sort: str = Query(default="created_at"),
    order: str = Query(default="desc"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    cursor: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """获取公开技能列表（支持 cursor 或 offset 分页）"""
    query = db.query(Skill).filter(Skill.is_public == True)

    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(Skill.name.ilike(like), Skill.description.ilike(like))
        )
    if category:
        query = query.filter(Skill.category == category)
    if tags:
        for tag in tags.split(","):
            tag = tag.strip()
            if tag:
                query = query.filter(Skill.tags.contains(tag))

    # Cursor-based pagination (优先)
    if cursor:
        cursor_data = decode_cursor(cursor)
        if cursor_data:
            cursor_id = cursor_data.get("id")
            cursor_created_at = cursor_data.get("created_at")
            if cursor_id and cursor_created_at:
                cursor_dt = datetime.fromisoformat(cursor_created_at)
                if order == "desc":
                    query = query.filter(
                        (Skill.created_at < cursor_dt)
                        | (Skill.created_at == cursor_dt, Skill.id < cursor_id)
                    )
                else:
                    query = query.filter(
                        (Skill.created_at > cursor_dt)
                        | (Skill.created_at == cursor_dt, Skill.id > cursor_id)
                    )

        sort_col = getattr(Skill, sort, Skill.created_at)
        if order == "asc":
            query = query.order_by(sort_col.asc(), Skill.id.asc())
        else:
            query = query.order_by(sort_col.desc(), Skill.id.desc())
    else:
        # Offset pagination (fallback)
        sort_col = getattr(Skill, sort, Skill.created_at)
        if order == "asc":
            query = query.order_by(sort_col.asc())
        else:
            query = query.order_by(sort_col.desc())

    total = query.count()

    # 如果使用 cursor 分页，不返回 total（前端不需要）
    if cursor:
        skills = query.limit(size).all()
        next_cursor = None
        if len(skills) == size:
            last = skills[-1]
            next_cursor = encode_cursor(last.id, last.created_at)
        return ok({
            "size": size,
            "items": [s.to_dict() for s in skills],
            "next_cursor": next_cursor,
        })
    else:
        # Offset pagination
        offset = (page - 1) * size
        skills = query.offset(offset).limit(size).all()
        pages = math.ceil(total / size) if size else 1
        return ok({
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
            "items": [s.to_dict() for s in skills],
        })


@router.get("/categories")
async def list_categories(db: Session = Depends(get_db)):
    """获取分类列表及数量"""
    total = db.query(Skill).filter(Skill.is_public == True).count()
    result = [{"name": "全部", "count": total}]
    for cat in CATEGORIES:
        count = db.query(Skill).filter(
            Skill.is_public == True, Skill.category == cat
        ).count()
        result.append({"name": cat, "count": count})
    return ok(result)


@router.get("/search")
async def search_skills(
    q: str = Query(default=None, min_length=1),
    category: Optional[str] = Query(default=None),
    tags: Optional[str] = Query(default=None),
    sort: str = Query(default="relevance"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    cursor: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    混合搜索：结合 FTS5 关键词搜索 + 向量语义搜索，使用 RRF 融合

    - q: 搜索查询字符串
    - category: 可选分类过滤
    - tags: 可选标签过滤（逗号分隔）
    - sort: relevance | star_count | created_at（默认 relevance 使用 RRF 融合）
    - page, size, cursor: 分页参数（cursor 优先）
    """
    if not q:
        # No query, fall back to regular list with cursor support
        query = db.query(Skill).filter(Skill.is_public == True)
        if category:
            query = query.filter(Skill.category == category)
        if tags:
            for tag in tags.split(","):
                tag = tag.strip()
                if tag:
                    query = query.filter(Skill.tags.contains(tag))

        if cursor:
            cursor_data = decode_cursor(cursor)
            if cursor_data:
                cursor_id = cursor_data.get("id")
                cursor_created_at = cursor_data.get("created_at")
                if cursor_id and cursor_created_at:
                    cursor_dt = datetime.fromisoformat(cursor_created_at)
                    query = query.filter(
                        (Skill.created_at < cursor_dt)
                        | (Skill.created_at == cursor_dt, Skill.id < cursor_id)
                    )
            query = query.order_by(Skill.created_at.desc(), Skill.id.desc())
            skills = query.limit(size).all()
            next_cursor = None
            if len(skills) == size:
                last = skills[-1]
                next_cursor = encode_cursor(last.id, last.created_at)
            return ok({
                "size": size,
                "items": [s.to_dict() for s in skills],
                "next_cursor": next_cursor,
            })
        else:
            total = query.count()
            offset = (page - 1) * size
            skills = query.order_by(Skill.created_at.desc()).offset(offset).limit(size).all()
            pages = math.ceil(total / size) if size else 1
            return ok({
                "total": total,
                "page": page,
                "size": size,
                "pages": pages,
                "items": [s.to_dict() for s in skills],
            })

    # Build base query for filters
    base_query = db.query(Skill.id).filter(Skill.is_public == True)
    if category:
        base_query = base_query.filter(Skill.category == category)
    if tags:
        for tag in tags.split(","):
            tag = tag.strip()
            if tag:
                base_query = base_query.filter(Skill.tags.contains(tag))

    # Get IDs that match filters
    filter_ids = [r[0] for r in base_query.all()]

    # 1. FTS5 keyword search
    fts_results = []
    with engine.connect() as conn:
        fts_query = text("""
            SELECT skill_id, name, description, tags FROM skills_fts
            WHERE skills_fts MATCH :query
        """)
        try:
            fts_results_raw = conn.execute(fts_query, {"query": q}).fetchall()
            # Score based on BM25
            for row in fts_results_raw:
                skill_id = row[0]
                name_text = row[1] or ""
                desc_text = row[2] or ""
                tags_text = row[3] or ""
                # Simple scoring: exact match in name > description > tags
                score = 0.0
                q_lower = q.lower()
                if q_lower in name_text.lower():
                    score += 10.0
                if q_lower in desc_text.lower():
                    score += 5.0
                if q_lower in tags_text.lower():
                    score += 3.0
                fts_results.append((skill_id, score))
        except Exception:
            # If FTS query fails, fall back to LIKE
            like_query = db.query(Skill).filter(
                Skill.is_public == True,
                or_(
                    Skill.name.ilike(f"%{q}%"),
                    Skill.description.ilike(f"%{q}%"),
                )
            )
            if category:
                like_query = like_query.filter(Skill.category == category)
            fts_results = [(s.id, 1.0) for s in like_query.all()]

    # 2. Vector semantic search (if embeddings exist)
    vector_results = []
    query_embedding = None
    try:
        query_embedding = text_to_embedding(q)
    except Exception:
        query_embedding = None

    if query_embedding is not None and filter_ids:
        # Get skills with embeddings that pass filters
        skills_with_embeddings = db.query(Skill).filter(
            Skill.is_public == True,
            Skill.embedding != None,
            Skill.id.in_(filter_ids) if filter_ids else True,
        ).all()

        for skill in skills_with_embeddings:
            try:
                sim = cosine_similarity(query_embedding, skill.embedding)
                vector_results.append((skill.id, sim))
            except Exception:
                pass

    # 3. RRF Fusion
    # Sort both result lists by score
    fts_sorted = sorted(fts_results, key=lambda x: x[1], reverse=True)
    vector_sorted = sorted(vector_results, key=lambda x: x[1], reverse=True)

    # RRF fusion
    fused = rrf_fusion([fts_sorted, vector_sorted])
    fused_ids = [item[0] for item in fused]

    # Build final results maintaining RRF order, then apply pagination
    total = len(fused_ids)
    offset = (page - 1) * size
    page_ids = fused_ids[offset:offset + size]

    # Fetch skills by order
    if page_ids:
        skills_ordered = db.query(Skill).filter(Skill.id.in_(page_ids)).all()
        # Maintain order from fused_ids
        skills_map = {s.id: s for s in skills_ordered}
        ordered_skills = [skills_map[sid] for sid in page_ids if sid in skills_map]
    else:
        ordered_skills = []

    pages = math.ceil(total / size) if size else 1
    return ok({
        "total": total,
        "page": page,
        "size": size,
        "pages": pages,
        "items": [s.to_dict() for s in ordered_skills],
    })


@router.get("/mine")
async def my_skills(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    """获取我的技能列表（需鉴权）"""
    query = db.query(Skill).filter(Skill.author_id == current_user.id)
    total = query.count()
    offset = (page - 1) * size
    skills = query.order_by(Skill.created_at.desc()).offset(offset).limit(size).all()
    pages = math.ceil(total / size) if size else 1

    return ok({
        "total": total,
        "page": page,
        "size": size,
        "pages": pages,
        "items": [s.to_dict() for s in skills],
    })


@router.get("/{skill_id}")
async def get_skill(
    skill_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """获取技能详情"""
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        return err_response(4004, "Skill not found", 404)

    is_starred = False
    is_author = False
    if current_user:
        is_author = skill.author_id == current_user.id
        star = db.query(SkillStar).filter(
            SkillStar.user_id == current_user.id,
            SkillStar.skill_id == skill_id,
        ).first()
        is_starred = star is not None

    return ok(skill.to_detail_dict(is_starred=is_starred, is_author=is_author))


@router.get("/{skill_id}/files/{filename}")
async def get_skill_file(
    skill_id: int,
    filename: str,
    db: Session = Depends(get_db),
):
    """获取技能文件内容"""
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        return err_response(4004, "Skill not found", 404)

    filename = safe_filename(filename)
    file_record = db.query(SkillFile).filter(
        SkillFile.skill_id == skill_id,
        SkillFile.filename == filename,
    ).first()
    if not file_record:
        return err_response(4004, "File not found", 404)

    file_path = file_record.file_path
    if not os.path.exists(file_path):
        return err_response(4004, "File not found on disk", 404)

    # Return text content for text-like files
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        # 记录审计日志
        log_audit(db, None, "skill_download", "skill_file", file_record.id, details={"skill_id": skill_id, "filename": filename})
        return PlainTextResponse(content)
    except UnicodeDecodeError:
        # 记录审计日志
        log_audit(db, None, "skill_download", "skill_file", file_record.id, details={"skill_id": skill_id, "filename": filename})
        return FileResponse(file_path)


@router.post("")
async def create_skill(
    name: str = Form(...),
    version: str = Form(...),
    description: Optional[str] = Form(default=None),
    category: Optional[str] = Form(default=None),
    tags: Optional[str] = Form(default="[]"),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    """上传新技能（需鉴权）"""
    # 名称格式校验
    if not re.match(r"^[a-zA-Z0-9\-]{2,100}$", name):
        return err_response(4002, "名称只允许字母、数字和连字符，如 my-skill")

    # 版本号格式
    if not re.match(r"^\d+\.\d+\.\d+$", version):
        return err_response(4002, "版本号格式应为 x.y.z，如 1.0.0")

    # 名称唯一性
    existing = db.query(Skill).filter(Skill.name == name).first()
    if existing:
        return err_response(4009, f"Skill name '{name}' already exists. Please choose a different name.")

    # 文件校验
    if not files:
        return err_response(4002, "请至少上传一个文件")

    total_size = 0
    for f in files:
        ext = os.path.splitext(f.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return err_response(
                4002,
                f"File type '{ext}' is not allowed. Allowed types: {' '.join(ALLOWED_EXTENSIONS)}"
            )
        content = await f.read()
        if len(content) > MAX_FILE_SIZE:
            return err_response(4002, f"File '{f.filename}' exceeds the 10MB limit.")
        total_size += len(content)
        await f.seek(0)

    if total_size > MAX_TOTAL_SIZE:
        return err_response(4002, "Total file size exceeds 50MB limit.")

    # 解析 tags
    try:
        tags_list = json.loads(tags) if tags else []
        if not isinstance(tags_list, list):
            tags_list = []
    except Exception:
        tags_list = []

    if len(tags_list) > 10:
        return err_response(4002, f"标签数量不能超过 10 个，当前 {len(tags_list)} 个")

    # 创建技能记录
    skill = Skill(
        name=name,
        version=version,
        description=description,
        category=category,
        tags=json.dumps(tags_list, ensure_ascii=False),
        is_public=True,
        author_id=current_user.id,
    )
    db.add(skill)
    db.flush()  # 获取 skill.id

    # 保存文件
    storage = get_storage()
    readme_content = None
    skill_md_content = None

    for f in files:
        content = await f.read()
        safe_name = safe_filename(f.filename)

        # 通过 StorageService 保存文件
        remote_key = f"skills/{skill.id}/{safe_name}"
        # 写入临时文件再上传
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            file_path = await storage.upload_file(tmp_path, remote_key)
        finally:
            os.unlink(tmp_path)

        # 提取 readme 和 skill_md
        fname_lower = safe_name.lower()
        try:
            text = content.decode("utf-8")
            if fname_lower == "readme.md":
                readme_content = text
            elif fname_lower == "skill.md":
                skill_md_content = text
        except UnicodeDecodeError:
            pass

        mime = _guess_mime(safe_name)
        file_record = SkillFile(
            skill_id=skill.id,
            filename=safe_name,
            file_path=file_path,
            file_size=len(content),
            mime_type=mime,
        )
        db.add(file_record)

    skill.readme = readme_content
    skill.skill_md = skill_md_content
    db.commit()
    db.refresh(skill)

# 记录审计日志
    log_audit(db, current_user.id, "skill_create", "skill", skill.id, details={"name": skill.name})

    return ok({
        "id": skill.id,
        "name": skill.name,
        "version": skill.version,
        "category": skill.category,
        "tags": skill.get_tags(),
        "author": {"login": current_user.login},
        "created_at": skill.created_at.isoformat() + "Z" if skill.created_at else None,
    }, "Skill uploaded successfully")


@router.delete("/{skill_id}")
async def delete_skill(
    skill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    """删除技能（需鉴权，仅限作者）"""
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        return err_response(4004, "Skill not found", 404)
    if skill.author_id != current_user.id:
        return err_response(4003, "Forbidden: You can only delete your own skills", 403)

    # 删除文件
    skill_upload_dir = os.path.join(UPLOAD_DIR, str(skill_id))
    if os.path.exists(skill_upload_dir):
        shutil.rmtree(skill_upload_dir)

    db.delete(skill)
    db.commit()

# 记录审计日志
    log_audit(db, current_user.id, "skill_delete", "skill", skill_id, details={"name": skill.name})

    return ok(None, "Skill deleted successfully")


@router.post("/{skill_id}/star")
async def star_skill(
    skill_id: int,
    rating: Optional[int] = Form(default=None, ge=1, le=10),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    """Star 技能（可选带评分 1-10）"""
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        return err_response(4004, "Skill not found", 404)

    existing = db.query(SkillStar).filter(
        SkillStar.user_id == current_user.id,
        SkillStar.skill_id == skill_id,
    ).first()

    if existing:
        # Update rating if provided
        if rating is not None and existing.rating is None:
            existing.rating = rating
            skill.rating_sum = (skill.rating_sum or 0) + rating
            skill.rating_count = (skill.rating_count or 0) + 1
            db.commit()
        return ok({"star_count": skill.star_count, "is_starred": True, "rating": existing.rating}, "Already starred")

    star = SkillStar(user_id=current_user.id, skill_id=skill_id, rating=rating)
    db.add(star)
    skill.star_count = (skill.star_count or 0) + 1
    if rating is not None:
        skill.rating_sum = (skill.rating_sum or 0) + rating
        skill.rating_count = (skill.rating_count or 0) + 1
    db.commit()
    db.refresh(skill)

    # 记录审计日志
    log_audit(db, current_user.id, "skill_star", "skill", skill_id, details={"name": skill.name, "rating": rating})

    return ok({"star_count": skill.star_count, "is_starred": True, "rating": rating}, "Starred successfully")


@router.delete("/{skill_id}/star")
async def unstar_skill(
    skill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    """取消 Star"""
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        return err_response(4004, "Skill not found", 404)

    existing = db.query(SkillStar).filter(
        SkillStar.user_id == current_user.id,
        SkillStar.skill_id == skill_id,
    ).first()

    if existing:
        db.delete(existing)
        skill.star_count = max(0, (skill.star_count or 1) - 1)
        db.commit()
        db.refresh(skill)

    # 记录审计日志
    log_audit(db, current_user.id, "skill_unstar", "skill", skill_id, details={"name": skill.name})

    return ok({"star_count": skill.star_count, "is_starred": False}, "Unstarred successfully")


@router.get("/{skill_id}/ratings")
async def get_skill_ratings(
    skill_id: int,
    db: Session = Depends(get_db),
):
    """获取技能评分统计"""
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        return err_response(4004, "Skill not found", 404)

    return ok({
        "average_rating": skill.average_rating,
        "rating_count": skill.rating_count,
        "star_count": skill.star_count,
    })


@router.get("/{skill_id}/versions")
async def list_skill_versions(
    skill_id: int,
    db: Session = Depends(get_db),
):
    """获取技能版本历史"""
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        return err_response(4004, "Skill not found", 404)

    versions = db.query(SkillVersion).filter(
        SkillVersion.skill_id == skill_id
    ).order_by(SkillVersion.created_at.desc()).all()

    return ok([v.to_dict() for v in versions])


@router.get("/{skill_id}/versions/{version}")
async def get_skill_version(
    skill_id: int,
    version: str,
    db: Session = Depends(get_db),
):
    """获取技能特定版本详情"""
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        return err_response(4004, "Skill not found", 404)

    skill_version = db.query(SkillVersion).filter(
        SkillVersion.skill_id == skill_id,
        SkillVersion.version == version,
    ).first()
    if not skill_version:
        return err_response(4004, "Version not found", 404)

    return ok(skill_version.to_dict())


@router.post("/{skill_id}/versions")
async def create_skill_version(
    skill_id: int,
    version: str = Form(...),
    description: Optional[str] = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    """创建新技能版本（需鉴权，仅限作者）"""
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        return err_response(4004, "Skill not found", 404)
    if skill.author_id != current_user.id:
        return err_response(4003, "Forbidden: You can only update your own skills", 403)

    # 版本号格式校验
    if not re.match(r"^\d+\.\d+\.\d+$", version):
        return err_response(4002, "版本号格式应为 x.y.z，如 1.0.0")

    # 检查版本是否已存在
    existing = db.query(SkillVersion).filter(
        SkillVersion.skill_id == skill_id,
        SkillVersion.version == version,
    ).first()
    if existing:
        return err_response(4009, f"Version {version} already exists")

    # 获取当前代码内容快照
    code_content = skill.skill_md or ""
    for f in skill.files:
        try:
            with open(f.file_path, "r", encoding="utf-8") as fp:
                code_content += f"\n\n# File: {f.filename}\n" + fp.read()
        except Exception:
            pass

    # 创建版本记录
    skill_version = SkillVersion(
        skill_id=skill_id,
        version=version,
        description=description,
        code_content=code_content,
        created_by=current_user.id,
    )
    db.add(skill_version)

    # 更新技能版本号
    skill.version = version
    db.commit()
    db.refresh(skill)

    return ok({"id": skill_version.id, "version": skill_version.version}, "Version created successfully")


@router.delete("/{skill_id}/versions/{version}")
async def delete_skill_version(
    skill_id: int,
    version: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    """删除指定版本（仅限作者）"""
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        return err_response(4004, "Skill not found", 404)
    if skill.author_id != current_user.id:
        return err_response(4003, "Forbidden: You can only update your own skills", 403)

    sv = db.query(SkillVersion).filter(
        SkillVersion.skill_id == skill_id,
        SkillVersion.version == version,
    ).first()
    if not sv:
        return err_response(4004, "Version not found", 404)

    db.delete(sv)
    db.commit()
    return ok({"version": version}, "Version deleted")


@router.post("/{skill_id}/versions/{version}/restore")
async def restore_skill_version(
    skill_id: int,
    version: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    """恢复旧版本为新版本（仅限作者）"""
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        return err_response(4004, "Skill not found", 404)
    if skill.author_id != current_user.id:
        return err_response(4003, "Forbidden: You can only update your own skills", 403)

    old = db.query(SkillVersion).filter(
        SkillVersion.skill_id == skill_id,
        SkillVersion.version == version,
    ).first()
    if not old:
        return err_response(4004, "Version not found", 404)

    latest = db.query(SkillVersion).filter(
        SkillVersion.skill_id == skill_id
    ).order_by(SkillVersion.created_at.desc()).first()

    parts = latest.version.split(".") if latest else [0, 0, 0]
    new_version = f"{int(parts[0])}.{int(parts[1])}.{int(parts[2]) + 1}"

    new_sv = SkillVersion(
        skill_id=skill_id,
        version=new_version,
        description=f"Restored from {version}",
        code_content=old.code_content,
        created_by=current_user.id,
    )
    db.add(new_sv)
    db.commit()
    db.refresh(new_sv)
    return ok({"new_version": new_version, "old_version": version}, "Version restored")


@router.get("/{skill_id}/versions/diff")
async def diff_skill_versions(
    skill_id: int,
    v1: str = Query(..., description="第一个版本号"),
    v2: str = Query(..., description="第二个版本号"),
    db: Session = Depends(get_db),
):
    """对比两个版本的代码差异"""
    import difflib

    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        return err_response(4004, "Skill not found", 404)

    sv1 = db.query(SkillVersion).filter(
        SkillVersion.skill_id == skill_id,
        SkillVersion.version == v1,
    ).first()
    sv2 = db.query(SkillVersion).filter(
        SkillVersion.skill_id == skill_id,
        SkillVersion.version == v2,
    ).first()
    if not sv1 or not sv2:
        return err_response(4004, "Version not found", 404)

    lines1 = sv1.code_content.splitlines() if sv1.code_content else []
    lines2 = sv2.code_content.splitlines() if sv2.code_content else []
    diff = list(difflib.unified_diff(lines1, lines2, fromfile=v1, tofile=v2, lineterm=""))

    return ok({
        "v1": v1,
        "v2": v2,
        "skill_id": skill_id,
        "diff": "\n".join(diff),
        "stats": {
            "v1_lines": len(lines1),
            "v2_lines": len(lines2),
            "additions": sum(1 for l in diff if l.startswith("+") and l not in ["+++", "+ "]),
            "deletions": sum(1 for l in diff if l.startswith("-") and l not in ["---", "- "]),
        },
    })


@router.get("/{skill_id}/analytics")
async def get_skill_analytics(
    skill_id: int,
    db: Session = Depends(get_db),
):
    """获取技能分析数据"""
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        return err_response(4004, "Skill not found", 404)

    return ok({
        "view_count": skill.view_count,
        "download_count": skill.download_count,
        "star_count": skill.star_count,
        "average_rating": skill.average_rating,
        "rating_count": skill.rating_count,
    })


@router.get("/analytics/leaderboard")
async def get_leaderboard(
    period: str = Query(default="week", pattern="^(week|month|all)$"),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """获取技能排行榜"""
    query = db.query(Skill).filter(Skill.is_public == True)

    # Sort by a composite score
    from sqlalchemy import case
    query = query.order_by(
        (Skill.star_count * 3 + Skill.download_count * 2 + Skill.view_count).desc()
    )

    skills = query.limit(limit).all()
    return ok([{
        "id": s.id,
        "name": s.name,
        "description": s.description,
        "category": s.category,
        "star_count": s.star_count,
        "download_count": s.download_count,
        "view_count": s.view_count,
        "average_rating": s.average_rating,
        "author": {
            "login": s.author.login,
            "avatar_url": s.author.avatar_url,
        } if s.author else None,
    } for s in skills])


def _guess_mime(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    mime_map = {
        ".py": "text/x-python",
        ".md": "text/markdown",
        ".txt": "text/plain",
        ".json": "application/json",
        ".yaml": "application/x-yaml",
        ".yml": "application/x-yaml",
        ".toml": "application/toml",
    }
    return mime_map.get(ext, "text/plain")
