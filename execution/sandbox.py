"""Wasm 沙箱隔离配置"""
from typing import Dict, List, Any
import os


class SandboxConfig:
    """沙箱隔离配置"""

    def __init__(self,
                 memory_limit_mb: int = 16,
                 time_limit_ms: int = 5000,
                 max_cpu_time_ms: int = 5000,
                 allowed_paths: List[str] = None,
                 forbidden_paths: List[str] = None):
        self.memory_limit_mb = memory_limit_mb
        self.time_limit_ms = time_limit_ms
        self.max_cpu_time_ms = max_cpu_time_ms
        self.allowed_paths = allowed_paths or ["/tmp", "/var/tmp"]
        self.forbidden_paths = forbidden_paths or [
            "/etc", "/usr", "/sys", "/dev", "/proc", "/var/log", "/root"
        ]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_limit_mb": self.memory_limit_mb,
            "time_limit_ms": self.time_limit_ms,
            "max_cpu_time_ms": self.max_cpu_time_ms,
            "allowed_paths": self.allowed_paths,
            "forbidden_paths": self.forbidden_paths,
        }


class Sandbox:
    """Wasm 执行沙箱主类"""

    def __init__(self, config: SandboxConfig = None):
        self.config = config or SandboxConfig()

    def is_path_allowed(self, path: str) -> bool:
        """检查路径是否允许访问"""
        # 检查是否在禁止列表中
        for fb in self.config.forbidden_paths:
            if path.startswith(fb):
                return False

        # 检查是否在允许列表中（如果有定义）
        if self.config.allowed_paths:
            return any(path.startswith(allowed) for allowed in self.config.allowed_paths)

        return True

    def validate_code(self, code: str) -> Dict[str, Any]:
        """
        验证代码安全性

        Args:
            code: 待验证代码

        Returns:
            {
                "valid": bool,
                "violations": [str],
                "warnings": [str]
            }
        """
        import re

        violations = []
        warnings = []

        # 危险函数检查
        dangerous_patterns = [
            ("exec(", "危险函数: exec()"),
            ("eval(", "危险函数: eval()"),
            ("__import__", "危险函数: __import__"),
            ("subprocess.call", "危险函数: subprocess.call"),
            ("os.system", "危险函数: os.system"),
            ("pty.spawn", "危险函数: pty.spawn"),
        ]

        for pattern, message in dangerous_patterns:
            if pattern in code:
                violations.append(message)

        # 路径检查
        paths = re.findall(r'["\']([/][^\s"\']+)["\']', code)
        for path in paths:
            if not self.is_path_allowed(path):
                violations.append(f"禁止路径访问: {path}")

        # 代码大小检查
        if len(code) > 100 * 1024:  # 100KB
            warnings.append("代码体积较大，可能影响执行性能")

        # 循环深度检查（简化版）
        loop_keywords = ["for ", "while ", " for", " while"]
        loop_count = sum(code.count(kw) for kw in loop_keywords)
        if loop_count > 100:
            warnings.append(f"检测到 {loop_count} 个循环，可能存在性能问题")

        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
        }

    def execute(self, code: str, context: dict = None) -> Dict[str, Any]:
        """
        在沙箱中执行代码

        Args:
            code: 代码字符串
            context: 执行上下文

        Returns:
            执行结果
        """
        # 前置验证
        validation = self.validate_code(code)
        if not validation["valid"]:
            return {
                "status": "rejected",
                "reason": "代码未通过安全验证",
                "violations": validation["violations"],
                "execution_time_ms": 0,
                "memory_usage_mb": 0,
            }

        # 执行代码
        from execution.wasmtime import WasmtimeSandbox

        sandbox = WasmtimeSandbox(
            memory_limit_mb=self.config.memory_limit_mb,
            time_limit_ms=self.config.time_limit_ms,
        )

        result = sandbox.execute(code)

        # 检查结果
        if not sandbox.verify_execution(result):
            return {
                "status": "exceeded_limits",
                "reason": "执行超出资源限制",
                "execution_time_ms": result.get("execution_time_ms", 0),
                "memory_usage_mb": result.get("memory_usage_mb", 0),
            }

        return result


# 默认沙箱配置
DEFAULT_SANDBOX = SandboxConfig()


def create_sandbox(config: Dict[str, Any] = None) -> Sandbox:
    """创建沙箱实例"""
    if config is None:
        return Sandbox(DEFAULT_SANDBOX)

    sandbox_config = SandboxConfig(
        memory_limit_mb=config.get("memory_limit_mb", 16),
        time_limit_ms=config.get("time_limit_ms", 5000),
        max_cpu_time_ms=config.get("max_cpu_time_ms", 5000),
        allowed_paths=config.get("allowed_paths"),
        forbidden_paths=config.get("forbidden_paths"),
    )

    return Sandbox(sandbox_config)