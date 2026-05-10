"""
数据库初始化与全局 Session 工厂
"""
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = os.getenv(
    "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'data', 'aetherhub.db')}"
)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    from .models import Base
    # Ensure data directory exists
    db_path = DATABASE_URL.replace("sqlite:///", "")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    Base.metadata.create_all(bind=engine)
    # Create FTS5 virtual table for full-text search
    _create_fts5_table(engine)


def _create_fts5_table(engine):
    """Create FTS5 virtual table for skill search if it doesn't exist"""
    from sqlalchemy import text
    with engine.connect() as conn:
        # Check if FTS table exists
        result = conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='skills_fts'"
        ))
        if not result.fetchone():
            # Create FTS5 virtual table for full-text search on skills
            # Using simple FTS5 without content sync for reliability
            conn.execute(text("""
                CREATE VIRTUAL TABLE IF NOT EXISTS skills_fts USING fts5(
                    skill_id,
                    name,
                    description,
                    tags
                )
            """))
            conn.commit()
            # Populate FTS table with existing data
            conn.execute(text("""
                INSERT INTO skills_fts(skill_id, name, description, tags)
                SELECT id, name, COALESCE(description, ''), COALESCE(tags, '') FROM skills
            """))
            conn.commit()


def rebuild_fts_index(engine):
    """Rebuild FTS index after skill changes"""
    from sqlalchemy import text
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM skills_fts"))
        conn.execute(text("""
            INSERT INTO skills_fts(skill_id, name, description, tags)
            SELECT id, name, COALESCE(description, ''), COALESCE(tags, '') FROM skills
        """))
        conn.commit()
