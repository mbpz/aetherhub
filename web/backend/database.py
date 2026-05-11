"""
数据库初始化与全局 Session 工厂
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

_engine = None


def get_engine():
    """Get or create database engine (lazy initialization)"""
    global _engine
    if _engine is None:
        DATABASE_URL = os.getenv(
            "DATABASE_URL",
            "postgresql://user:password@localhost:5432/aetherhub"
        )
        _engine = create_engine(
            DATABASE_URL,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
    return _engine


def get_session():
    """Get a new database session"""
    return SessionMaker(bind=get_engine())


# Backward compatibility: expose engine via property on this module
class _EngineProperty:
    """Descriptor to provide backward-compatible engine access."""
    def __get__(self, obj, objtype=None):
        return get_engine()


# For backward compatibility with code importing `engine`
engine = _EngineProperty()

SessionMaker = sessionmaker(autocommit=False, autoflush=False)


def init_db():
    from .models import Base
    Base.metadata.create_all(bind=get_engine())
