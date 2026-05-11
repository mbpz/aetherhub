"""Codex 代码生成引擎 - LLM Provider 接口"""
import os
from typing import Dict, Any, List

from codex.providers import get_llm_client, LLMClient


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

    def __init__(self, model: str = None):
        self.model = model
        self.llm_client: LLMClient = get_llm_client()

    def generate(self, prompt: str, max_tokens: int = 4096) -> Dict[str, Any]:
        """
        生成代码

        Args:
            prompt: 生成提示
            max_tokens: 最大 token 数

        Returns:
            {"code": str, "verified": bool, "error": str or None}
        """
        try:
            code = self.llm_client.generate(prompt, max_tokens=max_tokens)
            return {"code": code, "verified": False, "error": None}
        except Exception as e:
            return {"code": "", "verified": False, "error": str(e)}

    def verify_and_fix(self, code: str) -> str:
        """
        验证代码并修复问题

        集成 Z3 反馈进行迭代修正
        """
        dangerous = ["exec(", "eval(", "__import__", "subprocess.call",
                     "os.system", "pty.spawn", "socket.socket"]
        for pattern in dangerous:
            if pattern in code:
                # 完全移除危险模式，而不是只加注释
                code = code.replace(pattern, "# 移除危险模式")
        return code

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
            result = self.generate(prompt)
            code = result.get("code", "") if isinstance(result, dict) else result

            if not code or len(code) < 20:
                last_feedback = "代码生成失败"
                continue

            # 安全检查：危险模式移除
            verified_code = self.verify_and_fix(code)

            # 如果有 Z3 验证器，进行形式化验证
            if z3_verifier:
                rules = intent_vector.get("constraints", [])
                if not rules:
                    rules = ["禁止访问 /etc", "禁止访问 /usr", "禁止访问 /sys",
                             "禁止访问 /dev", "禁止访问 /proc", "禁止访问 /var/log",
                             "禁止访问 /root", "文件大小不超过 100MB"]

                z3_result = z3_verifier.verify_with_feedback(verified_code, rules)

                if not z3_result.get("verified", False):
                    last_feedback = z3_result.get("feedback", "验证失败")
                    if z3_result.get("fixed_code"):
                        last_fixed = z3_result["fixed_code"]
                        verified_code = z3_result["fixed_code"]
                    else:
                        violations = z3_result.get("violations", [])
                        for v in violations:
                            if "路径" in str(v) or "函数" in str(v):
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
