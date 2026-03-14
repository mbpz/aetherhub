"""
AetherHub FastAPI 主应用
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .routes import auth as auth_router
from .routes import skills as skills_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动时初始化数据库并写入 seed 数据"""
    init_db()
    # 自动写入 seed 数据（仅开发环境）
    if os.getenv("AUTO_SEED", "true").lower() == "true":
        try:
            from .seed import seed
            seed()
        except Exception as e:
            print(f"⚠️  Seed failed (non-fatal): {e}")
    yield


app = FastAPI(
    title="AetherHub API",
    description="AetherHub - 大模型技能管理平台 API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router.router, prefix="/api/v1")
app.include_router(skills_router.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "AetherHub API is running", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("web.backend.main:app", host="0.0.0.0", port=8000, reload=True)
