"""DeepSeek LLM adapter"""
import os
from typing import Optional

from codex.providers.base import LLMClient

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

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


class DeepSeekAdapter(LLMClient):
    """DeepSeek API adapter"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or DEEPSEEK_API_KEY
        self.model = model or DEEPSEEK_MODEL
        self.client = None
        self._init_client()

    def _init_client(self):
        """Initialize DeepSeek client"""
        if self.api_key and OpenAI:
            try:
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url="https://api.deepseek.com"
                )
            except Exception:
                self.client = None

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate code from prompt using DeepSeek API"""
        if not self.client:
            return self._mock_generate(prompt)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=kwargs.get("max_tokens", 4096),
                temperature=kwargs.get("temperature", 0.2),
            )
            code = response.choices[0].message.content
            # Clean markdown code blocks
            if code.startswith("```"):
                lines = code.split("\n")
                code = "\n".join(lines[1:] if lines[0] == "```python" else lines)
                code = code.rstrip("```").rstrip("```python")
            return code
        except Exception as e:
            # API call failed, fall back to mock
            return self._mock_generate(prompt, error=str(e))

    def _mock_generate(self, prompt: str, error: Optional[str] = None) -> str:
        """Mock mode when no API key or API call fails"""
        intent_line = ""
        skills_line = ""

        for line in prompt.split("\n"):
            if "意图向量:" in line or "intent_vector" in line.lower():
                intent_line = line
            if "原子技能:" in line or "atomic_skills" in line.lower():
                skills_line = line

        if "write_file" in skills_line or "写入" in intent_line:
            return '''"""生成的技能代码"""
import csv
from typing import List, Optional
import os


def write_csv_safe(filepath: str, data: List[dict], max_size_mb: int = 100) -> str:
    """安全写入 CSV 文件"""
    forbidden = ["/etc", "/usr", "/sys", "/dev", "/proc", "/var/log", "/root"]
    for path in forbidden:
        if filepath.startswith(path):
            raise ValueError(f"禁止写入系统目录: {path}")

    estimated_size = len(str(data)) * len(data)
    if estimated_size > max_size_mb * 1024 * 1024:
        raise ValueError(f"文件大小超过限制: {max_size_mb}MB")

    os.makedirs(os.path.dirname(filepath) or "/tmp", exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        if data:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    return filepath


def filter_data(data: List[dict], condition: str) -> List[dict]:
    """根据条件过滤数据"""
    filtered = []
    for row in data:
        try:
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
    """安全读取 CSV 文件"""
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
    """处理数据"""
    if operation == "filter":
        return [x for x in data if x]
    elif operation == "map":
        return [x for x in data]
    return data
'''
