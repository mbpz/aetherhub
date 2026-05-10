"""ISMP 约束注入模块"""
from typing import Dict, List, Any


class ConstraintInjector:
    """约束动态注入 — 根据资源类型生成 Z3 安全约束"""

    def inject(self, intent_vector: Dict[str, Any],
               code: str) -> Dict[str, Any]:
        """
        动态注入安全约束

        Args:
            intent_vector: 语义向量化结果
            code: 生成的代码

        Returns:
            constraints: {
                "resource_type": str,
                "rules": [str],         # 供 Z3 验证的规则列表
                "z3_constraints": [Z3],  # Z3 表达式
                "max_size": int,
                "metadata": {}
            }
        """
        resource_type = intent_vector.get("object", "unknown")

        constraints = {
            "resource_type": resource_type,
            "rules": [],
            "z3_constraints": [],
            "metadata": {},
        }

        if resource_type == "file":
            constraints = self._inject_file_constraints(intent_vector, code, constraints)
        elif resource_type == "database":
            constraints = self._inject_database_constraints(intent_vector, code, constraints)
        elif resource_type == "network":
            constraints = self._inject_network_constraints(intent_vector, code, constraints)

        return constraints

    def _inject_file_constraints(self, intent_vector: Dict[str, Any],
                                 code: str,
                                 constraints: Dict[str, Any]) -> Dict[str, Any]:
        """为文件操作注入约束"""
        from ismp.capability import CapabilitySpace
        cap_space = CapabilitySpace()
        rules = cap_space.get_resource_rules("file")

        # 路径禁止规则
        for path in rules.get("forbidden_paths", []):
            constraints["rules"].append(f"禁止访问 {path}")

        # 文件大小限制
        max_size = rules.get("max_size", 0)
        constraints["max_size"] = max_size
        constraints["rules"].append(f"文件大小不超过 {max_size // (1024*1024)}MB")

        # 生成 Z3 约束
        constraints["z3_constraints"] = self._build_path_constraints(rules["forbidden_paths"])

        # 检查代码中是否直接引用了禁止路径
        for path in rules["forbidden_paths"]:
            if path in code:
                constraints["metadata"]["violation"] = f"代码中包含禁止路径: {path}"

        return constraints

    def _inject_database_constraints(self, intent_vector: Dict[str, Any],
                                       code: str,
                                       constraints: Dict[str, Any]) -> Dict[str, Any]:
        """为数据库操作注入约束"""
        from ismp.capability import CapabilitySpace
        cap_space = CapabilitySpace()
        rules = cap_space.get_resource_rules("database")

        # 操作禁止规则
        for op in rules.get("forbidden_operations", []):
            constraints["rules"].append(f"禁止 {op} 操作")

        # 表禁止规则
        for table in rules.get("forbidden_tables", []):
            constraints["rules"].append(f"禁止访问表 {table}")

        constraints["z3_constraints"] = self._build_database_constraints(
            rules["forbidden_operations"]
        )

        return constraints

    def _inject_network_constraints(self, intent_vector: Dict[str, Any],
                                     code: str,
                                     constraints: Dict[str, Any]) -> Dict[str, Any]:
        """为网络操作注入约束"""
        from ismp.capability import CapabilitySpace
        cap_space = CapabilitySpace()
        rules = cap_space.get_resource_rules("network")

        # 域名禁止规则
        for domain in rules.get("forbidden_domains", []):
            constraints["rules"].append(f"禁止访问域名 {domain}")

        # IP 禁止规则
        for ip in rules.get("forbidden_ips", []):
            constraints["rules"].append(f"禁止访问 IP {ip}")

        if rules.get("require_https"):
            constraints["rules"].append("必须使用 HTTPS")

        constraints["z3_constraints"] = self._build_network_constraints(
            rules["forbidden_domains"],
            rules["forbidden_ips"]
        )

        return constraints

    def _build_path_constraints(self, forbidden_paths: List[str]) -> list:
        """构建路径 Z3 约束（返回结构化数据，由 z3_verifier 转换为 Z3 表达式）"""
        return [
            {"type": "forbidden_paths", "paths": forbidden_paths}
        ]

    def _build_database_constraints(self, forbidden_ops: List[str]) -> list:
        """构建数据库 Z3 约束"""
        return [
            {"type": "forbidden_operations", "ops": forbidden_ops}
        ]

    def _build_network_constraints(self, forbidden_domains: List[str],
                                   forbidden_ips: List[str]) -> list:
        """构建网络 Z3 约束"""
        return [
            {"type": "forbidden_domains", "domains": forbidden_domains},
            {"type": "forbidden_ips", "ips": forbidden_ips},
        ]

    def extract_code_paths(self, code: str) -> List[str]:
        """从代码中提取所有文件路径引用"""
        import re
        path_pattern = r'["\']([/][^\s"\']+)["\']'
        paths = re.findall(path_pattern, code)
        return paths

    def check_path_violations(self, paths: List[str]) -> List[str]:
        """检查路径是否违反安全规则"""
        from ismp.capability import CapabilitySpace
        cap_space = CapabilitySpace()
        rules = cap_space.get_resource_rules("file")
        forbidden = rules.get("forbidden_paths", [])

        violations = []
        for path in paths:
            for fb in forbidden:
                if path.startswith(fb):
                    violations.append(f"{path} 违反规则: 禁止访问 {fb}")
        return violations