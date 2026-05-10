"""Tree-sitter → Z3 公式转换层

可选依赖：tree-sitter + tree-sitter-python
降级方案：使用 Python 内置 ast 模块
"""
from typing import Any, List, Optional
import ast
import re

# 尝试导入 tree-sitter（可选依赖）
try:
    import tree_sitter
    from tree_sitter import Language, Parser
    from tree_sitter_python import language as py_language
    _TREE_SITTER_AVAILABLE = True
except ImportError:
    _TREE_SITTER_AVAILABLE = False


def _get_tree_sitter_parser():
    """获取 Tree-sitter parser（如果可用）"""
    if not _TREE_SITTER_AVAILABLE:
        return None

    try:
        lang_obj = Language(py_language())
        parser = Parser(lang_obj)
        return parser
    except Exception:
        return None


# Tree-sitter parser 实例
_PARSER = None


def _get_parser():
    """获取或初始化 Tree-sitter parser"""
    global _PARSER
    if _PARSER is None:
        _PARSER = _get_tree_sitter_parser()
    return _PARSER


def code_to_ast(code: str) -> Any:
    """
    将 Python 代码解析为 AST（优先使用 Tree-sitter，降级到 Python ast）

    Args:
        code: Python 代码字符串

    Returns:
        AST 根节点（Tree-sitter 或 Python ast）
    """
    parser = _get_parser()
    if parser is not None:
        try:
            tree = parser.parse(bytes(code, "utf8"))
            return tree.root_node
        except Exception:
            pass

    # 降级到 Python ast
    return ast.parse(code)


def ast_to_z3_formula(node) -> Any:
    """
    将 AST 节点递归转换为 Z3 表达式

    Args:
        node: AST 节点（Tree-sitter 或 Python ast）

    Returns:
        Z3 表达式（Int, Bool, 或其组合）
    """
    from z3 import Int, Bool, And, Or, Implies, If, sat, unsat

    # Tree-sitter 节点
    if hasattr(node, 'type'):
        return _tree_sitter_node_to_z3(node)

    # Python ast 节点
    if isinstance(node, ast.AST):
        return _python_ast_to_z3(node)

    return Bool("unknown")


def _tree_sitter_node_to_z3(node) -> Any:
    """将 Tree-sitter AST 节点递归转换为 Z3 表达式"""
    from z3 import Int, Bool, And, Or, Implies, If

    node_type = node.type

    # 模块/函数定义
    if node_type in ("module", "function_definition"):
        for child in node.children:
            result = _tree_sitter_node_to_z3(child)
            if result is not None:
                return result
        return Bool("defined")

    # 赋值语句: x = y + 1
    if node_type == "assignment":
        children = node.children
        if len(children) >= 3:
            var_node = children[0]
            value_node = children[2]
            if var_node.type == "identifier":
                var_name = var_node.text.decode()
                var = Int(var_name)
                value_expr = _tree_sitter_node_to_z3(value_node)
                if value_expr is not None:
                    return var == value_expr
        return Bool("assignment")

    # 标识符
    if node_type == "identifier":
        name = node.text.decode()
        return Int(name)

    # 整数常量
    if node_type in ("integer", "decimal_integer"):
        try:
            val = int(node.text.decode())
            return val
        except:
            return Int(0)

    # 字符串常量
    if node_type == "string":
        val = node.text.decode().strip('"').strip("'")
        return val

    # 比较运算符
    if node_type in ("binary_operator", "comparison_operator"):
        children = node.children
        if len(children) >= 3:
            left = _tree_sitter_node_to_z3(children[0])
            op = children[1].text.decode()
            right = _tree_sitter_node_to_z3(children[2])

            if op == "+":
                return left + right
            elif op == "-":
                return left - right
            elif op == "*":
                return left * right
            elif op == "/":
                return left / right
            elif op == ">":
                return left > right
            elif op == "<":
                return left < right
            elif op == ">=":
                return left >= right
            elif op == "<=":
                return left <= right
            elif op == "==":
                return left == right
            elif op == "!=":
                return left != right
            elif op in ("and", "&&"):
                return And(left, right)
            elif op in ("or", "||"):
                return Or(left, right)

    # if 语句
    if node_type == "if_statement":
        # 找到 condition 和 block
        for i, child in enumerate(node.children):
            if child.type == "comparison_operator":
                return _tree_sitter_node_to_z3(child)
        return Bool("if_condition")

    # for 循环
    if node_type == "for_statement":
        return Bool("for_loop")

    # while 循环
    if node_type == "while_statement":
        for child in node.children:
            if child.type == "comparison_operator":
                return _tree_sitter_node_to_z3(child)
        return Bool("while_loop")

    # 函数调用
    if node_type == "call":
        func_name = None
        for child in node.children:
            if child.type == "identifier":
                func_name = child.text.decode()
                break
        return Bool(f"call_{func_name or 'fn'}")

    # return 语句
    if node_type == "return_statement":
        for child in node.children:
            if child.type not in ("return",):
                return _tree_sitter_node_to_z3(child)
        return Bool("return")

    # 块内容
    if node_type == "block":
        results = []
        for child in node.children:
            result = _tree_sitter_node_to_z3(child)
            if result is not None:
                results.append(result)
        if results:
            return And(results) if len(results) > 1 else results[0]
        return Bool("block")

    # 未知节点
    return Bool(f"unknown_{node_type}")


def _python_ast_to_z3(node: ast.AST) -> Any:
    """将 Python AST 节点转换为 Z3 表达式"""
    from z3 import Int, Bool, And, Or, If

    if isinstance(node, ast.Assign):
        if len(node.targets) == 1:
            var_name = _get_var_name(node.targets[0])
            if var_name:
                var = Int(var_name)
                value = _python_ast_to_z3(node.value)
                if value:
                    return var == value
        return Bool("assignment")

    elif isinstance(node, ast.BinOp):
        left = _python_ast_to_z3(node.left)
        right = _python_ast_to_z3(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        elif isinstance(node.op, ast.Sub):
            return left - right
        elif isinstance(node.op, ast.Mult):
            return left * right
        elif isinstance(node.op, ast.Div):
            return left / right
        return Bool("binop")

    elif isinstance(node, ast.Compare):
        left = _python_ast_to_z3(node.left)
        if len(node.comparators) == 1:
            right = _python_ast_to_z3(node.comparators[0])
            op = node.ops[0]
            if isinstance(op, ast.Gt):
                return left > right
            elif isinstance(op, ast.Lt):
                return left < right
            elif isinstance(op, ast.GtE):
                return left >= right
            elif isinstance(op, ast.LtE):
                return left <= right
            elif isinstance(op, ast.Eq):
                return left == right
            elif isinstance(op, ast.NotEq):
                return left != right
        return Bool("compare")

    elif isinstance(node, ast.Name):
        return Int(node.id)

    elif isinstance(node, ast.Constant):
        if isinstance(node.value, int):
            return node.value
        elif isinstance(node.value, str):
            return node.value
        return Int(0)

    elif isinstance(node, ast.If):
        test = _python_ast_to_z3(node.test)
        return test  # 简化：返回条件

    elif isinstance(node, ast.While):
        test = _python_ast_to_z3(node.test)
        return test

    elif isinstance(node, ast.For):
        return Bool("for_loop")

    elif isinstance(node, ast.Call):
        func_name = _get_func_name(node.func)
        return Bool(f"call_{func_name}")

    elif isinstance(node, ast.Module):
        results = []
        for child in node.body:
            result = _python_ast_to_z3(child)
            if result:
                results.append(result)
        return And(results) if results else Bool("module")

    elif isinstance(node, ast.FunctionDef):
        return Bool(f"def_{node.name}")

    elif isinstance(node, ast.Return):
        if node.value:
            return _python_ast_to_z3(node.value)
        return Bool("return")

    return Bool(f"unknown_{type(node).__name__}")


def _get_var_name(node) -> str:
    """从 AST 节点获取变量名"""
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _get_func_name(node) -> str:
    """从 AST 节点获取函数名"""
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        return node.attr
    return "unknown"


def extract_all_constraints(code: str) -> List[Any]:
    """
    从代码中提取所有可验证的约束

    Args:
        code: Python 代码

    Returns:
        Z3 约束列表
    """
    tree = code_to_ast(code)
    constraints = []

    def walk(node):
        try:
            if hasattr(node, 'type'):
                # Tree-sitter node
                node_type = node.type
                if node_type in ("assignment", "if_statement", "for_statement", "while_statement", "comparison_operator"):
                    result = _tree_sitter_node_to_z3(node)
                    if result is not None:
                        constraints.append(result)
            elif isinstance(node, ast.AST):
                # Python AST node
                if isinstance(node, (ast.Assign, ast.If, ast.While, ast.For, ast.Compare)):
                    result = _python_ast_to_z3(node)
                    if result is not None:
                        constraints.append(result)

            # Walk children
            if hasattr(node, 'children'):
                for child in node.children:
                    walk(child)
            elif hasattr(node, 'body'):
                for child in node.body:
                    walk(child)
            elif hasattr(node, 'orelse'):
                for child in node.orelse:
                    walk(child)
        except Exception:
            pass  # 忽略无法处理的节点

    walk(tree)
    return constraints


def verify_code_safety(code: str, constraints: List[str]) -> dict:
    """
    对代码进行形式化安全验证

    Args:
        code: Python 代码
        constraints: 安全约束列表

    Returns:
        验证结果 {
            "verified": bool,
            "formula": str,
            "counterexample": str or None,
            "constraints_checked": int
        }
    """
    from z3 import Solver, unsat

    # 提取代码逻辑约束
    code_constraints = extract_all_constraints(code)

    # 构建安全规则
    security_rules = build_security_rules(constraints)

    # 创建求解器
    solver = Solver()

    # 添加代码约束
    for c in code_constraints:
        try:
            solver.add(c)
        except Exception:
            pass  # 忽略无效约束

    # 添加安全规则（逆约束，检测违规）
    solver.add(Not(And(security_rules)))

    result = solver.check()

    if result == unsat:
        return {
            "verified": True,
            "formula": str(code_constraints),
            "counterexample": None,
            "constraints_checked": len(code_constraints),
        }
    else:
        model = solver.model()
        return {
            "verified": False,
            "formula": str(code_constraints),
            "counterexample": str(model),
            "constraints_checked": len(code_constraints),
        }


def build_security_rules(constraints: List[str]) -> Any:
    """将约束字符串列表构建为 Z3 表达式"""
    from z3 import Bool, And

    if not constraints:
        return [Bool("True")]

    rules = []
    for constraint in constraints:
        if "禁止访问" in constraint:
            rules.append(Bool("path_allowed"))
        else:
            rules.append(Bool("rule_hold"))

    return rules if rules else [Bool("True")]


def validate_code_against_rules(code: str, rules: List[str]) -> dict:
    """使用 Z3 验证代码是否符合规则"""
    return verify_code_safety(code, rules)