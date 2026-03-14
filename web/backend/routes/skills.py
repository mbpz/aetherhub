"""
Skill 路由：CRUD + 搜索 + Star
"""
import json
import math
import os
import re
import shutil
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse, PlainTextResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from ..deps import get_db, get_optional_user, require_user
from ..models import Skill, SkillFile, SkillStar, User

router = APIRouter(prefix="/skills", tags=["skills"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_TOTAL_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml"}

CATEGORIES = ["数据处理", "网络工具", "文件操作", "AI工具", "系统工具", "其他"]


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
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """获取公开技能列表"""
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

    total = query.count()

    sort_col = getattr(Skill, sort, Skill.created_at)
    if order == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

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
        return PlainTextResponse(content)
    except UnicodeDecodeError:
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
    skill_upload_dir = os.path.join(UPLOAD_DIR, str(skill.id))
    os.makedirs(skill_upload_dir, exist_ok=True)

    readme_content = None
    skill_md_content = None

    for f in files:
        content = await f.read()
        safe_name = safe_filename(f.filename)
        file_path = os.path.join(skill_upload_dir, safe_name)
        with open(file_path, "wb") as fp:
            fp.write(content)

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
    return ok(None, "Skill deleted successfully")


@router.post("/{skill_id}/star")
async def star_skill(
    skill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    """Star 技能"""
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        return err_response(4004, "Skill not found", 404)

    existing = db.query(SkillStar).filter(
        SkillStar.user_id == current_user.id,
        SkillStar.skill_id == skill_id,
    ).first()

    if existing:
        return ok({"star_count": skill.star_count, "is_starred": True}, "Already starred")

    star = SkillStar(user_id=current_user.id, skill_id=skill_id)
    db.add(star)
    skill.star_count = (skill.star_count or 0) + 1
    db.commit()
    db.refresh(skill)

    return ok({"star_count": skill.star_count, "is_starred": True}, "Starred successfully")


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

    return ok({"star_count": skill.star_count, "is_starred": False}, "Unstarred successfully")


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
