"""Wasm 执行沙箱 - Wasmtime + Python 模拟双模式

- Wasm 字节码 → wasmtime 真实执行（需预先编译）
- Python 代码字符串 → 模拟安全执行（安全分析 + 估算结果）

安装 wasmtime: pip install wasmtime
"""
from typing import Dict, Any
import time
import re

try:
    import wasmtime
    from wasmtime import Engine, Linker, Module, Store
except ImportError:
    wasmtime = None
    Engine = Linker = Module = Store = None


class WasmtimeSandbox:
    """Wasm 执行沙箱"""

    def __init__(self, memory_limit_mb: int = 16, time_limit_ms: int = 5000):
        self.memory_limit = memory_limit_mb * 1024 * 1024  # bytes
        self.time_limit = time_limit_ms
        self._engine = Engine() if wasmtime else None

    def execute(self, code: str) -> Dict[str, Any]:
        """
        执行代码

        Args:
            code: Wasm 字节码（\\x00\\x61\\x73\\x6d 开头）或 Python 代码字符串

        Returns:
            执行结果
        """
        # 检测是否为 Wasm 字节码
        is_wasm = (
            isinstance(code, bytes) and len(code) > 4 and code[:4] == b"\x00\x61\x73\x6d"
        ) or (
            isinstance(code, str) and len(code) > 4 and code[:4].encode().hex() == "0061736d"
        )

        if is_wasm:
            wasm_bytes = code if isinstance(code, bytes) else code.encode()
            if wasmtime and self._engine:
                return self._execute_wasm(wasm_bytes)
            return {"status": "error", "output": "wasmtime not available", "execution_time_ms": 0, "memory_usage_mb": 0}
        else:
            # Python 代码：模拟安全执行
            return self._simulate_execution(code)

    def _execute_wasm(self, wasm_code: bytes) -> Dict[str, Any]:
        """真实 Wasm 执行"""
        if not wasmtime:
            return {"status": "error", "output": "wasmtime not installed", "execution_time_ms": 0, "memory_usage_mb": 0}

        start_time = time.time()
        try:
            engine = Engine()
            module = Module(engine, wasm_code)
            linker = Linker(engine)
            linker.define_wasi()
            store = Store(engine)
            instance = linker.instantiate(store, module)
            exports = instance.exports(store)
            if hasattr(exports, "run"):
                result = exports.run(store)
                return {
                    "status": "success",
                    "output": str(result),
                    "execution_time_ms": int((time.time() - start_time) * 1000),
                    "memory_usage_mb": self._estimate_memory(store),
                }
            return {
                "status": "success",
                "output": "Wasm module loaded",
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "memory_usage_mb": 1,
            }
        except Exception as e:
            return {
                "status": "error",
                "output": str(e),
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "memory_usage_mb": 0,
            }

    def _simulate_execution(self, code: str) -> Dict[str, Any]:
        """模拟执行 Python 代码（安全模式）"""
        start_time = time.time()
        safety = self._analyze_safety(code)

        if not safety["is_safe"]:
            return {
                "status": "blocked",
                "output": f"代码包含危险模式，已被安全沙箱拦截: {safety['dangerous_patterns']}",
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "memory_usage_mb": 0,
                "blocked": True,
            }

        # 估算执行时间和内存
        lines = len(code.split("\n"))
        estimated_time = min(int((time.time() - start_time) * 1000) + lines * 2, self.time_limit)
        estimated_memory = min(1 + lines // 100, self.memory_limit // (1024 * 1024))

        return {
            "status": "success",
            "output": f"Python 代码模拟执行完成（{lines} 行）",
            "execution_time_ms": estimated_time,
            "memory_usage_mb": estimated_memory,
            "simulated": True,
            "safety": safety,
        }

    def _analyze_safety(self, code: str) -> Dict[str, Any]:
        """分析代码安全性"""
        dangerous_patterns = [
            ("exec(", "危险函数: exec()"),
            ("eval(", "危险函数: eval()"),
            ("__import__", "危险函数: __import__"),
            ("subprocess.call", "危险函数: subprocess.call"),
            ("os.system", "危险函数: os.system"),
            ("pty.spawn", "危险函数: pty.spawn"),
        ]

        found = []
        for pattern, msg in dangerous_patterns:
            if pattern in code:
                found.append(msg)

        # 检查路径访问
        import os
        paths = re.findall(r'["\']([/][^\s"\']+)["\']', code)
        forbidden = [p for p in paths if any(p.startswith(f) for f in [
            "/etc", "/usr", "/sys", "/dev", "/proc", "/var/log", "/root"
        ])]

        return {
            "dangerous_patterns": found,
            "forbidden_paths_accessed": forbidden,
            "is_safe": len(found) == 0 and len(forbidden) == 0,
        }

    def _estimate_memory(self, store) -> float:
        """估算内存使用"""
        try:
            if hasattr(store, "memory"):
                mem = store.memory
                if mem:
                    return round(mem.data_size() / (1024 * 1024), 2)
        except Exception:
            pass
        return 1.0

    def verify_execution(self, result: Dict[str, Any]) -> bool:
        """验证执行结果是否在安全范围内"""
        if result.get("blocked", False):
            return False
        if result.get("execution_time_ms", 0) > self.time_limit:
            return False
        memory_mb = result.get("memory_usage_mb", 0)
        limit_mb = self.memory_limit / (1024 * 1024)
        if memory_mb > limit_mb:
            return False
        return True

    def execute_with_isolation(self, code: str,
                               allowed_paths: list = None) -> Dict[str, Any]:
        """在隔离环境中执行（路径限制）"""
        if allowed_paths is None:
            allowed_paths = ["/tmp"]

        paths = re.findall(r'["\']([/][^\s"\']+)["\']', code)
        for path in paths:
            if not any(path.startswith(a) for a in allowed_paths):
                return {
                    "status": "blocked",
                    "output": f"路径访问受限: {path}（仅允许: {allowed_paths}）",
                    "execution_time_ms": 0,
                    "memory_usage_mb": 0,
                    "blocked": True,
                }

        return self.execute(code)
