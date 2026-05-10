"""ISMP 语义向量化模块"""
from typing import Dict, Any
import re


class SemanticVectorizer:
    """语义向量化 — 将自然语言意图解析为结构化向量"""

    # 动词映射表（中英文）
    VERB_PATTERNS = {
        "write": ["write", "导出", "写入", "保存", "输出"],
        "read": ["read", "读取", "读入", "获取"],
        "execute": ["execute", "执行", "运行"],
        "filter": ["filter", "过滤", "筛选"],
        "delete": ["delete", "删除", "移除"],
        "update": ["update", "更新", "修改"],
        "search": ["search", "搜索", "查找"],
    }

    # 条件模式
    CONDITION_PATTERNS = [
        (r"年龄\s*>\s*\d+", "age_gt"),
        (r"年龄\s*<\s*\d+", "age_lt"),
        (r"年龄\s*>=\s*\d+", "age_gte"),
        (r"年龄\s*<=\s*\d+", "age_lte"),
        (r"年龄\s*==\s*\d+", "age_eq"),
        (r">\s*(\d+)", "gt"),
        (r"<\s*(\d+)", "lt"),
    ]

    # 对象类型识别
    OBJECT_PATTERNS = {
        "file": [r"/[^\s]+", r"\.(csv|txt|json|yaml|xml|py)$"],
        "database": [r"database", r"db", r"表", r"table"],
        "api": [r"api", r"http", r"url", r"endpoint"],
        "memory": [r"memory", r"buffer", r"cache"],
    }

    def vectorize(self, intent: str) -> Dict[str, Any]:
        """
        将用户意图解析为结构化向量

        Args:
            intent: 用户意图字符串

        Returns:
            intent_vector: {
                "verb": str,       # write/read/execute/filter/delete/update/search
                "object": str,     # file/database/api/memory/unknown
                "target": str,     # 文件路径或资源标识
                "condition": str,   # 条件表达式
                "constraints": []   # 额外约束列表
            }
        """
        intent_lower = intent.lower()
        result = {
            "verb": "unknown",
            "object": "unknown",
            "target": None,
            "condition": None,
            "constraints": [],
            "raw_intent": intent,
        }

        # 1. 提取动词
        result["verb"] = self._extract_verb(intent_lower)

        # 2. 提取目标路径/标识
        result["target"] = self._extract_target(intent, intent_lower)

        # 3. 识别对象类型
        result["object"] = self._extract_object_type(intent_lower)

        # 4. 提取条件
        result["condition"] = self._extract_condition(intent)

        return result

    def _extract_verb(self, intent_lower: str) -> str:
        """从意图中提取动词"""
        for verb, patterns in self.VERB_PATTERNS.items():
            if any(p in intent_lower for p in patterns):
                return verb
        return "unknown"

    def _extract_target(self, intent: str, intent_lower: str) -> str | None:
        """提取目标路径或资源标识"""
        # 提取 Unix 路径
        path_pattern = r'(/[^\s]+)'
        paths = re.findall(path_pattern, intent)
        if paths:
            return paths[0]

        # 提取引号包裹的字符串
        quoted = re.findall(r'["\']([^"\']+)["\']', intent)
        if quoted:
            return quoted[0]

        return None

    def _extract_object_type(self, intent_lower: str) -> str:
        """识别对象类型"""
        for obj_type, patterns in self.OBJECT_PATTERNS.items():
            if any(re.search(p, intent_lower) for p in patterns):
                return obj_type
        return "unknown"

    def _extract_condition(self, intent: str) -> str | None:
        """提取条件表达式"""
        for pattern, label in self.CONDITION_PATTERNS:
            match = re.search(pattern, intent)
            if match:
                return match.group(0)
        return None

    def extract_constraints_from_intent(self, intent: str) -> list:
        """从意图中提取额外的安全约束"""
        constraints = []
        intent_lower = intent.lower()

        # 大小限制
        if any(kw in intent_lower for kw in ["小于", "不超过", "最大", "limit"]):
            size_match = re.search(r'(\d+)\s*(MB|KB|GB)', intent, re.I)
            if size_match:
                constraints.append(f"max_size:{size_match.group(1)}{size_match.group(2)}")

        # 时间限制
        if any(kw in intent_lower for kw in ["秒", "分钟内", "超时"]):
            time_match = re.search(r'(\d+)\s*秒', intent)
            if time_match:
                constraints.append(f"max_time:{time_match.group(1)}s")

        return constraints