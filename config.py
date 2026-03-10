"""配置文件"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """配置类"""

    # Codex 配置
    CODEX_MODEL = os.getenv("CODEX_MODEL", "codex-3.5")
    CODEX_MAX_TOKENS = int(os.getenv("CODEX_MAX_TOKENS", 4096))

    # Z3 配置
    Z3_TIMEOUT = int(os.getenv("Z3_TIMEOUT", 30))

    # Wasm 执行配置
    WASM_MEMORY_LIMIT = int(os.getenv("WASM_MEMORY_LIMIT", 16))  # MB
    WASM_TIME_LIMIT = int(os.getenv("WASM_TIME_LIMIT", 5000))  # ms

    # 安全规则配置
    MAX_LOOP_DEPTH = int(os.getenv("MAX_LOOP_DEPTH", 1000))
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 100 * 1024 * 1024))  # 100MB
