"""ISMP 能力空间管理模块"""
from typing import Dict, List, Any


class CapabilitySpace:
    """能力空间 — 管理原子技能注册表和资源规则"""

    # 原子技能定义
    ATOMIC_SKILLS = {
        "read_file": {
            "description": "读取指定路径的文件内容",
            "params": ["path"],
            "security_level": "low",
        },
        "write_file": {
            "description": "写入内容到指定文件",
            "params": ["path", "content"],
            "security_level": "medium",
        },
        "read_database": {
            "description": "从数据库读取数据",
            "params": ["query"],
            "security_level": "medium",
        },
        "write_database": {
            "description": "向数据库写入数据",
            "params": ["query", "data"],
            "security_level": "high",
        },
        "read_api": {
            "description": "发起 GET 请求获取 API 数据",
            "params": ["url"],
            "security_level": "medium",
        },
        "write_api": {
            "description": "发起 POST/PUT 请求提交数据",
            "params": ["url", "data", "method"],
            "security_level": "high",
        },
        "execute_command": {
            "description": "执行系统命令",
            "params": ["command"],
            "security_level": "critical",
        },
        "execute_script": {
            "description": "执行脚本文件",
            "params": ["script_path"],
            "security_level": "high",
        },
        "filter_data": {
            "description": "根据条件过滤数据",
            "params": ["data", "condition"],
            "security_level": "low",
        },
        "filter_stream": {
            "description": "对数据流进行过滤处理",
            "params": ["stream", "condition"],
            "security_level": "low",
        },
        "filesystem_list": {
            "description": "列出目录内容",
            "params": ["dir_path"],
            "security_level": "low",
        },
        "filesystem_mkdir": {
            "description": "创建目录",
            "params": ["dir_path"],
            "security_level": "medium",
        },
    }

    # 能力空间动词映射
    VERB_TO_SKILLS = {
        "read": ["read_file", "read_database", "read_api"],
        "write": ["write_file", "write_database", "write_api"],
        "execute": ["execute_command", "execute_script"],
        "filter": ["filter_data", "filter_stream"],
        "delete": ["execute_command"],  # 通过命令执行删除
        "update": ["write_database", "write_file"],
        "search": ["read_file", "read_api", "filter_data"],
    }

    # 资源类型安全规则
    RESOURCE_RULES = {
        "file": {
            "forbidden_paths": ["/etc", "/usr", "/sys", "/dev", "/proc", "/var/log", "/root"],
            "max_size": 100 * 1024 * 1024,  # 100MB
            "allowed_extensions": [".csv", ".txt", ".json", ".yaml", ".py", ".md"],
        },
        "database": {
            "forbidden_operations": ["DROP", "DELETE", "UPDATE", "TRUNCATE", "ALTER"],
            "forbidden_tables": ["system", "admin", "users", "passwords"],
            "read_only": False,
        },
        "network": {
            "forbidden_domains": ["malicious.com", "phishing.com", ".onion"],
            "forbidden_ips": ["192.168.1.1", "10.0.0.1", "127.0.0.1"],
            "require_https": True,
        },
        "memory": {
            "max_alloc_mb": 512,
            "max_duration_ms": 5000,
        },
    }

    def __init__(self):
        self.capability_space = self.ATOMIC_SKILLS.copy()
        self.verb_to_skills = self.VERB_TO_SKILLS.copy()
        self.resource_rules = self.RESOURCE_RULES.copy()

    def map_intent_to_skills(self, intent_vector: Dict[str, Any]) -> List[str]:
        """
        将意图向量映射为原子技能列表

        Args:
            intent_vector: 语义向量化结果

        Returns:
            原子技能名称列表
        """
        verb = intent_vector.get("verb", "unknown")
        object_type = intent_vector.get("object", "unknown")

        skills = []

        # 基础技能映射
        if verb in self.verb_to_skills:
            skills.extend(self.verb_to_skills[verb])

        # 根据对象类型调整技能
        if object_type == "file" and "execute_command" in skills:
            # 文件操作不涉及命令执行
            skills = [s for s in skills if s not in ["execute_command", "execute_script"]]

        # 特殊处理：写文件需要先读
        if verb == "write" and object_type == "file":
            if "write_file" in skills and "read_file" not in skills:
                skills.insert(0, "read_file")
            if "filter_data" not in skills:
                skills.append("filter_data")

        # 去除重复
        return list(dict.fromkeys(skills))

    def get_security_level(self, skill_name: str) -> str:
        """获取技能的安全等级"""
        skill = self.ATOMIC_SKILLS.get(skill_name, {})
        return skill.get("security_level", "unknown")

    def get_resource_rules(self, resource_type: str) -> Dict[str, Any]:
        """获取资源类型的安全规则"""
        return self.resource_rules.get(resource_type, {})

    def get_capabilities(self) -> List[str]:
        """获取所有可用能力"""
        return list(self.ATOMIC_SKILLS.keys())