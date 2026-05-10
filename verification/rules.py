"""Z3 安全规则集"""
from typing import Dict, List, Any


# 文件系统安全规则
FILE_RULES = {
    "forbidden_paths": ["/etc", "/usr", "/sys", "/dev", "/proc", "/var/log", "/root"],
    "max_file_size": 100 * 1024 * 1024,  # 100MB
    "allowed_extensions": [".csv", ".txt", ".json", ".yaml", ".yml", ".xml", ".py", ".md"],
}

# 数据库安全规则
DATABASE_RULES = {
    "forbidden_operations": ["DROP", "DELETE", "UPDATE", "TRUNCATE", "ALTER", "CREATE"],
    "forbidden_tables": ["system", "admin", "users", "passwords", "auth"],
    "read_only_mode": False,
}

# 网络安全规则
NETWORK_RULES = {
    "forbidden_domains": ["malicious.com", "phishing.com", ".onion", "darknet"],
    "forbidden_ips": ["192.168.1.1", "10.0.0.1", "127.0.0.1", "0.0.0.0"],
    "require_https": True,
    "max_response_size": 10 * 1024 * 1024,  # 10MB
}

# 代码质量规则
CODE_QUALITY_RULES = {
    "max_loop_depth": 1000,
    "max_function_calls": 10000,
    "no_exec": True,
    "no_eval": True,
    "no_import_os": False,  # 允许但不推荐
    "no_import_subprocess": False,
}

# 资源限制规则
RESOURCE_RULES = {
    "max_memory_mb": 512,
    "max_cpu_time_ms": 5000,
    "max_disk_read_mb": 100,
    "max_disk_write_mb": 50,
}


def get_rules_for_resource(resource_type: str) -> Dict[str, Any]:
    """根据资源类型获取对应规则"""
    mapping = {
        "file": FILE_RULES,
        "database": DATABASE_RULES,
        "network": NETWORK_RULES,
    }
    return mapping.get(resource_type, {})


def rule_to_z3_constraint(rule: Dict[str, Any], resource_type: str) -> List[Any]:
    """
    将规则转换为 Z3 约束列表

    Args:
        rule: 规则字典
        resource_type: 资源类型

    Returns:
        Z3 表达式列表
    """
    from z3 import Int, String, And, Or, Not, sat, unsat

    constraints = []

    if resource_type == "file":
        # 路径约束
        path_var = Int("path_idx")
        forbidden_indices = [Int(f"forbidden_{i}") for i in range(len(rule.get("forbidden_paths", [])))]
        # 约束: path_idx 不能是禁止路径的索引
        # 注意：这里我们检查的是路径字符串，而非索引
        constraints.append(Not(path_var in forbidden_indices))

        # 文件大小约束
        size_var = Int("file_size")
        max_size = rule.get("max_file_size", 100 * 1024 * 1024)
        constraints.append(size_var <= max_size)

    elif resource_type == "database":
        # 操作约束
        op_var = Int("operation_code")
        forbidden_ops = [Int(f"op_{i}") for i in range(len(rule.get("forbidden_operations", [])))]
        constraints.append(Not(op_var in forbidden_ops))

    return constraints


def validate_code_against_rules(code: str, rules: Dict[str, Any]) -> Dict[str, Any]:
    """
    用规则验证代码，返回验证结果

    Args:
        code: 待验证代码
        rules: 安全规则

    Returns:
        {
            "passed": bool,
            "violations": [str],
            "checked_rules": int
        }
    """
    violations = []
    checked = 0

    # 检查文件路径
    if "file" in rules:
        import re
        for fb in rules["file"].get("forbidden_paths", []):
            checked += 1
            pattern = re.escape(fb)
            if re.search(pattern, code):
                violations.append(f"代码包含禁止路径: {fb}")

    # 检查禁止操作
    if "database" in rules:
        for op in rules["database"].get("forbidden_operations", []):
            checked += 1
            if op in code.upper():
                violations.append(f"代码包含禁止操作: {op}")

    # 检查网络
    if "network" in rules:
        for domain in rules["network"].get("forbidden_domains", []):
            checked += 1
            if domain in code:
                violations.append(f"代码包含禁止域名: {domain}")

    # 检查危险函数
    dangerous_funcs = ["exec(", "eval(", "__import__", "subprocess"]
    for func in dangerous_funcs:
        checked += 1
        if func in code:
            violations.append(f"代码包含危险函数: {func}")

    return {
        "passed": len(violations) == 0,
        "violations": violations,
        "checked_rules": checked,
    }