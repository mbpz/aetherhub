"""
AetherHub 数据模型 - SQLAlchemy ORM
"""
import json
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    ForeignKey, UniqueConstraint, create_engine
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    github_id = Column(Integer, unique=True, nullable=False)
    login = Column(String(100), nullable=False)
    name = Column(String(200))
    avatar_url = Column(Text)
    email = Column(String(200))
    bio = Column(Text)
    html_url = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    skills = relationship("Skill", back_populates="author", cascade="all, delete-orphan")
    stars = relationship("SkillStar", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "github_id": self.github_id,
            "login": self.login,
            "name": self.name,
            "avatar_url": self.avatar_url,
            "email": self.email,
            "bio": self.bio,
            "html_url": self.html_url,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
        }


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, unique=True)
    description = Column(Text)
    readme = Column(Text)
    skill_md = Column(Text)
    version = Column(String(50), default="1.0.0")
    category = Column(String(100))
    tags = Column(Text, default="[]")  # JSON array string
    is_public = Column(Boolean, default=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    download_count = Column(Integer, default=0)
    star_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    author = relationship("User", back_populates="skills")
    files = relationship("SkillFile", back_populates="skill", cascade="all, delete-orphan")
    stars = relationship("SkillStar", back_populates="skill", cascade="all, delete-orphan")

    def get_tags(self):
        try:
            return json.loads(self.tags) if self.tags else []
        except Exception:
            return []

    def to_dict(self, include_author=True):
        d = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "category": self.category,
            "tags": self.get_tags(),
            "is_public": self.is_public,
            "star_count": self.star_count,
            "download_count": self.download_count,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
            "updated_at": self.updated_at.isoformat() + "Z" if self.updated_at else None,
        }
        if include_author and self.author:
            d["author"] = {
                "id": self.author.id,
                "login": self.author.login,
                "name": self.author.name,
                "avatar_url": self.author.avatar_url,
                "html_url": self.author.html_url,
            }
        return d

    def to_detail_dict(self, is_starred=False, is_author=False):
        d = self.to_dict(include_author=True)
        d["readme"] = self.readme
        d["skill_md"] = self.skill_md
        d["is_starred"] = is_starred
        d["is_author"] = is_author
        d["files"] = [f.to_dict() for f in self.files]
        return d


class SkillFile(Base):
    __tablename__ = "skill_files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    filename = Column(String(200), nullable=False)
    file_path = Column(Text, nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    created_at = Column(DateTime, default=func.now())

    skill = relationship("Skill", back_populates="files")

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
        }


class SkillStar(Base):
    __tablename__ = "skill_stars"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="stars")
    skill = relationship("Skill", back_populates="stars")

    __table_args__ = (
        UniqueConstraint("user_id", "skill_id", name="uq_user_skill_star"),
    )


def get_engine(database_url: str):
    return create_engine(database_url, connect_args={"check_same_thread": False})


def get_session_factory(engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db(engine):
    Base.metadata.create_all(bind=engine)
