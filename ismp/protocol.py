"""ISMP 协议核心实现"""
from typing import Dict, List, Any
import time
import datetime

from ismp.semantic import SemanticVectorizer
from ismp.capability import CapabilitySpace
from ismp.constraint import ConstraintInjector


class ISMPProtocol:
    """ISMP 协议主类"""

    def __init__(self, codex_engine, tree_sitter, z3_verifier):
        self.codex = codex_engine
        self.tree_sitter = tree_sitter
        self.z3 = z3_verifier

        # 初始化子模块
        self.semantic = SemanticVectorizer()
        self.capability = CapabilitySpace()
        self.constraint = ConstraintInjector()

    def process(self, intent: str) -> Dict[str, Any]:
        """
        处理用户意图，返回技能产物

        Args:
            intent: 用户意图字符串

        Returns:
            技能产物字典
        """
        # Step 1: 语义向量化
        intent_vector = self.semantic.vectorize(intent)

        # Step 2: 能力空间匹配
        atomic_skills = self.capability.map_intent_to_skills(intent_vector)

        # Step 3: 逻辑合成
        code = self._logic_synthesis(intent_vector, atomic_skills)

        # Step 4: 约束注入
        constraints = self.constraint.inject(intent_vector, code)

        # Step 5: 证明打包
        artifact = self._pack_artifact(intent_vector, atomic_skills, code, constraints)

        return artifact

    def _logic_synthesis(self, intent_vector: Dict[str, Any],
                         atomic_skills: List[str]) -> str:
        """
        情境感知逻辑合成

        使用 Codex 生成代码（带验证重试循环）
        """
        max_attempts = 3
        last_error = None

        for attempt in range(max_attempts):
            try:
                # 使用 generate_with_verification 获取带验证的代码
                result = self.codex.generate_with_verification(
                    intent_vector,
                    atomic_skills
                )

                code = result.get("code", "")
                verified = result.get("verified", False)

                # 如果代码未通过验证且有修复建议，使用修复后的代码
                if not verified and "fixed_code" in result:
                    code = result["fixed_code"]

                if code and len(code) > 50:
                    return code

            except Exception as e:
                last_error = str(e)

            # 验证失败或代码无效，重试
            if attempt < max_attempts - 1:
                continue

        # All attempts failed - raise error instead of returning mock
        raise RuntimeError(
            f"Codex failed to generate code after {max_attempts} attempts. "
            f"Last error: {last_error}. Ensure Codex engine is available."
        )

    def _pack_artifact(self, intent_vector: Dict[str, Any],
                       atomic_skills: List[str], code: str,
                       constraints: Dict[str, Any]) -> Dict[str, Any]:
        """
        证明携带式产物打包

        打包技能产物和验证证明
        """
        artifact = {
            "artifact_id": f"art_{int(time.time())}",
            "intent": str(intent_vector.get("raw_intent", "")),
            "intent_vector": intent_vector,
            "atomic_skills": atomic_skills,
            "code": code,
            "constraints": constraints,
            "metadata": {
                "generated_at": datetime.datetime.now().isoformat(),
                "codex_model": getattr(self.codex, "model", "unknown"),
                "verification_result": "pending"
            }
        }

        return artifact