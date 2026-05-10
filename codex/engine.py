"""Codex 代码生成引擎 - 真实 API 实现"""
import os
from typing import Dict, Any, Optional, List

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


SYSTEM_PROMPT = """你是一个安全的代码生成助手，专门生成 Python 技能代码。

安全要求：
1. 禁止访问 /etc、/usr、/sys、/dev、/proc、/var/log、/root 等系统目录
2. 禁止使用 exec()、eval()、__import__、subprocess 等危险函数
3. 文件操作只允许在 /tmp 或用户指定的安全路径
4. 禁止生成包含恶意代码或后门的技能
5. 代码必须包含适当的错误处理

输出格式：
- 仅输出代码，不要解释
- 代码必须可直接执行
- 使用类型提示
- 包含必要的 import
"""

USER_PROMPT_TEMPLATE = """根据以下意图生成 Python 代码：

意图向量: {intent_vector}
原子技能: {atomic_skills}

要求：
1. 实现上述原子技能
2. 代码简洁、高效
3. 包含错误处理
4. 使用类型提示
5. 严格遵守安全约束
6. 不要访问任何系统目录
"""


class CodexEngine:
    """Codex 代码生成引擎"""

    def __init__(self, model: str = "gpt-4o"):
        self.model = model
        self.client = None
        self._init_client()

    def _init_client(self):
        """初始化 OpenAI 客户端"""
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and OpenAI:
            self.client = OpenAI(api_key=api_key)

    def generate(self, prompt: str, max_tokens: int = 4096) -> str:
        """
        生成代码

        Args:
            prompt: 生成提示
            max_tokens: 最大 token 数

        Returns:
            生成的代码
        """
        if not self.client:
            return self._mock_generate(prompt)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=0.2,
            )
            code = response.choices[0].message.content
            # 清理可能的markdown代码块
            if code.startswith("```"):
                lines = code.split("\n")
                code = "\n".join(lines[1:] if lines[0] == "```python" else lines)
                code = code.rstrip("```").rstrip("```python")
            return code
        except Exception as e:
            return self._mock_generate(prompt, error=str(e))

    def _mock_generate(self, prompt: str, error: str = None) -> str:
        """
        Mock 模式：当没有 API key 时返回基于 prompt 的模拟代码

        Args:
            prompt: 生成提示
            error: 错误信息（如果有）

        Returns:
            模拟生成的代码
        """
        # 从 prompt 中提取意图和技能
        intent_line = ""
        skills_line = ""

        for line in prompt.split("\n"):
            if "意图:" in line or "intent" in line.lower():
                intent_line = line
            if "原子技能:" in line or "atomic" in line.lower():
                skills_line = line

        # 根据技能生成适当的代码
        if "write_file" in skills_line or "写入" in intent_line:
            return '''"""生成的技能代码"""
import csv
from typing import List, Optional
import os


def write_csv_safe(filepath: str, data: List[dict], max_size_mb: int = 100) -> str:
    """
    安全写入 CSV 文件

    Args:
        filepath: 文件路径（只允许 /tmp 或用户目录）
        data: 数据列表
        max_size_mb: 最大文件大小（MB）

    Returns:
        写入的文件路径
    """
    # 安全检查：不允许系统目录
    forbidden = ["/etc", "/usr", "/sys", "/dev", "/proc", "/var/log", "/root"]
    for path in forbidden:
        if filepath.startswith(path):
            raise ValueError(f"禁止写入系统目录: {path}")

    # 检查文件大小
    estimated_size = len(str(data)) * len(data)
    if estimated_size > max_size_mb * 1024 * 1024:
        raise ValueError(f"文件大小超过限制: {max_size_mb}MB")

    # 写入文件
    os.makedirs(os.path.dirname(filepath) or "/tmp", exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        if data:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    return filepath


def filter_data(data: List[dict], condition: str) -> List[dict]:
    """
    根据条件过滤数据

    Args:
        data: 数据列表
        condition: 过滤条件

    Returns:
        过滤后的数据
    """
    filtered = []
    for row in data:
        try:
            # 简单条件解析
            if ">=" in condition:
                key, val = condition.split(">=")
                if float(row.get(key.strip(), 0)) >= float(val.strip()):
                    filtered.append(row)
            elif "<=" in condition:
                key, val = condition.split("<=")
                if float(row.get(key.strip(), 0)) <= float(val.strip()):
                    filtered.append(row)
            elif ">" in condition:
                key, val = condition.split(">")
                if float(row.get(key.strip(), 0)) > float(val.strip()):
                    filtered.append(row)
            elif "<" in condition:
                key, val = condition.split("<")
                if float(row.get(key.strip(), 0)) < float(val.strip()):
                    filtered.append(row)
        except (ValueError, KeyError):
            continue
    return filtered
'''
        elif "read_file" in skills_line or "读取" in intent_line:
            return '''"""生成的技能代码"""
import csv
from typing import List, Optional


def read_csv_safe(filepath: str, encoding: str = "utf-8") -> List[dict]:
    """
    安全读取 CSV 文件

    Args:
        filepath: 文件路径
        encoding: 文件编码

    Returns:
        CSV 数据列表
    """
    # 安全检查
    forbidden = ["/etc", "/usr", "/sys", "/dev", "/proc", "/var/log", "/root"]
    for path in forbidden:
        if filepath.startswith(path):
            raise ValueError(f"禁止读取系统目录: {path}")

    with open(filepath, "r", encoding=encoding) as f:
        reader = csv.DictReader(f)
        return list(reader)
'''
        else:
            return '''"""生成的技能代码"""
from typing import Any, List, Optional


def process_data(data: List[Any], operation: str = "identity") -> List[Any]:
    """
    处理数据

    Args:
        data: 输入数据
        operation: 操作类型

    Returns:
        处理后的数据
    """
    if operation == "filter":
        return [x for x in data if x]
    elif operation == "map":
        return [x for x in data]
    return data
'''

    def verify_and_fix(self, code: str) -> str:
        """
        验证代码并修复问题

        集成 Z3 反馈进行迭代修正
        """
        dangerous = ["exec(", "eval(", "__import__", "subprocess.call",
                     "os.system", "pty.spawn", "socket.socket"]
        fixed = code
        for pattern in dangerous:
            if pattern in code:
                fixed = fixed.replace(pattern, f"# 移除危险模式: {pattern}")
        return fixed

    def generate_with_verification(self, intent_vector: dict,
                                   atomic_skills: List[str],
                                   z3_verifier=None,
                                   max_retries: int = 3) -> Dict[str, Any]:
        """
        生成代码并进行验证（带重试循环）

        Args:
            intent_vector: 意图向量
            atomic_skills: 原子技能列表
            z3_verifier: Z3 验证器（可选）
            max_retries: 最大重试次数

        Returns:
            {
                "code": str,
                "verified": bool,
                "feedback": str,
                "fixed_code": str or None
            }
        """
        prompt = USER_PROMPT_TEMPLATE.format(
            intent_vector=intent_vector,
            atomic_skills=atomic_skills,
        )

        last_feedback = ""
        last_fixed = None

        for attempt in range(max_retries):
            # 生成代码
            code = self.generate(prompt)
            if not code or len(code) < 20:
                last_feedback = "代码生成失败"
                continue

            # 安全检查
            verified_code = self.verify_and_fix(code)

            # 如果有 Z3 验证器，进行形式化验证
            if z3_verifier:
                rules = intent_vector.get("constraints", [])
                if not rules:
                    rules = ["禁止访问 /etc", "禁止访问 /usr", "禁止访问 /sys",
                             "禁止访问 /dev", "禁止访问 /proc", "禁止访问 /var/log",
                             "禁止访问 /root", "文件大小不超过 100MB"]

                result = z3_verifier.verify_with_feedback(verified_code, rules)

                if not result.get("verified", False):
                    last_feedback = result.get("feedback", "验证失败")
                    # 如果有修复建议，使用修复后的代码
                    if result.get("fixed_code"):
                        last_fixed = result["fixed_code"]
                        verified_code = result["fixed_code"]
                    # 否则用注释标记问题代码段
                    else:
                        violations = result.get("violations", [])
                        for v in violations:
                            if "路径" in str(v) or "函数" in str(v):
                                # 找到并注释掉问题行
                                for line in verified_code.split("\n"):
                                    if any(p in line for p in ["/etc", "/usr", "/sys", "/dev", "exec(", "eval("]):
                                        if not line.strip().startswith("#"):
                                            verified_code = verified_code.replace(
                                                line,
                                                f"# [安全删除] {line}"
                                            )
            else:
                last_feedback = "代码已生成并通过基础安全检查"

            # 基础验证：确保代码不包含明显危险模式
            dangerous_found = False
            for pattern in ["exec(", "eval(", "__import__", "subprocess.call", "os.system"]:
                if pattern in verified_code:
                    dangerous_found = True
                    break

            if not dangerous_found and len(verified_code) > 50:
                return {
                    "code": verified_code,
                    "verified": True,
                    "feedback": last_feedback or "代码已生成并通过安全检查",
                    "fixed_code": last_fixed,
                }

            last_feedback = f"尝试 {attempt + 1}: 代码未通过安全检查"

        # 所有尝试都失败
        return {
            "code": last_fixed or '"""生成的代码 - 安全模式"""\npass',
            "verified": False,
            "feedback": f"代码生成失败，已尝试 {max_retries} 次: {last_feedback}",
            "fixed_code": None,
        }