"""Codex 代码模板库"""
from typing import Dict, List


# 安全约束模板
SECURITY_TEMPLATES = {
    "path_restriction": '''
# 路径安全约束
FORBIDDEN_PATHS = {forbidden_paths}
def check_path(path):
    for fb in FORBIDDEN_PATHS:
        if path.startswith(fb):
            raise ValueError(f"禁止访问: {{path}}")
    return True
''',
    "size_limit": '''
# 文件大小约束
MAX_SIZE = {max_size}  # bytes
def check_size(size):
    if size > MAX_SIZE:
        raise ValueError(f"文件大小超过限制: {{MAX_SIZE}}")
    return True
''',
    "operation_whitelist": '''
# 操作白名单
ALLOWED_OPS = {allowed_ops}
def check_operation(op):
    if op not in ALLOWED_OPS:
        raise ValueError(f"操作不允许: {{op}}")
    return True
''',
}

# 原子技能代码模板
ATOMIC_SKILL_TEMPLATES = {
    "read_file": '''
import os
from typing import Optional

def read_file(path: str, encoding: str = "utf-8") -> str:
    """读取文件内容"""
    # 安全检查
    forbidden = ["/etc", "/usr", "/sys", "/dev", "/proc", "/var/log", "/root"]
    for fb in forbidden:
        if path.startswith(fb):
            raise ValueError(f"禁止读取系统目录: {{fb}}")
    if not os.path.exists(path):
        raise FileNotFoundError(f"文件不存在: {{path}}")
    with open(path, "r", encoding=encoding) as f:
        return f.read()
''',

    "write_file": '''
import os

def write_file(path: str, content: str, encoding: str = "utf-8") -> str:
    """写入文件内容"""
    # 安全检查
    forbidden = ["/etc", "/usr", "/sys", "/dev", "/proc", "/var/log", "/root"]
    for fb in forbidden:
        if path.startswith(fb):
            raise ValueError(f"禁止写入系统目录: {{fb}}")
    # 检查磁盘空间
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding=encoding) as f:
            f.write(content)
    except Exception as e:
        raise IOError(f"写入失败: {{e}}")
    return path
''',

    "filter_data": '''
from typing import List, Callable, Any

def filter_data(data: List[Any], condition: Callable[[Any], bool]) -> List[Any]:
    """过滤数据"""
    return [item for item in data if condition(item)]

def filter_by_comparison(data: List[dict], key: str, op: str, value: Any) -> List[dict]:
    """根据比较条件过滤数据"""
    ops = {{
        ">": lambda a, b: a > b,
        "<": lambda a, b: a < b,
        ">=": lambda a, b: a >= b,
        "<=": lambda a, b: a <= b,
        "==": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
    }}
    if op not in ops:
        raise ValueError(f"不支持的操作: {{op}}")
    return [row for row in data if key in row and ops[op](row[key], value)
''',

    "execute_command": '''
import subprocess
from typing import List

# 允许的命令白名单
ALLOWED_COMMANDS = ["ls", "cat", "head", "tail", "grep", "awk", "sed"]

def safe_execute(command: str, args: List[str]) -> str:
    """安全执行命令"""
    if command not in ALLOWED_COMMANDS:
        raise ValueError(f"命令不允许: {{command}}")
    try:
        result = subprocess.run(
            [command] + args,
            capture_output=True,
            text=True,
            timeout=10,
            cwd="/tmp",
        )
        return result.stdout
    except subprocess.TimeoutExpired:
        raise TimeoutError("命令执行超时")
    except Exception as e:
        raise RuntimeError(f"命令执行失败: {{e}}")
''',
}


def get_template(skill_name: str) -> str:
    """获取技能模板"""
    return ATOMIC_SKILL_TEMPLATES.get(skill_name, "")


def build_security_prompt() -> str:
    """构建安全提示词"""
    return """
安全约束：
1. 禁止访问 /etc、/usr、/sys、/dev、/proc、/var/log、/root
2. 禁止使用 exec()、eval()、__import__、subprocess（除白名单命令外）
3. 文件操作只允许在 /tmp 或用户目录
4. 所有路径必须通过安全检查函数
5. 包含适当的异常处理

安全检查函数：
def check_path(path):
    forbidden = ["/etc", "/usr", "/sys", "/dev", "/proc", "/var/log", "/root"]
    for fb in forbidden:
        if path.startswith(fb):
            raise ValueError(f"禁止访问: {{path}}")

def check_size(size, max_size=100*1024*1024):
    if size > max_size:
        raise ValueError(f"文件大小超过限制")
"""


def generate_skill_code(skills: List[str], context: dict) -> str:
    """
    根据技能列表生成完整代码

    Args:
        skills: 技能名称列表
        context: 上下文信息

    Returns:
        生成的完整代码
    """
    parts = ['"""生成的技能代码"""']

    # 添加安全检查函数
    parts.append(SECURITY_TEMPLATES["path_restriction"].format(
        forbidden_paths=["/etc", "/usr", "/sys", "/dev", "/proc", "/var/log", "/root"]
    ))
    parts.append(SECURITY_TEMPLATES["size_limit"].format(
        max_size=100 * 1024 * 1024
    ))

    # 添加技能实现
    for skill in skills:
        template = get_template(skill)
        if template:
            parts.append(template)

    return "\n\n".join(parts)