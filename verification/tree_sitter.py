"""Tree-sitter 集成模块 - AST 解析和逻辑公式提取"""
from typing import Dict, List, Any, Optional
from z3 import Bool, Int, Real, And, Or, Not, Implies, sat, unsat

try:
    import tree_sitter
    from tree_sitter import Language, Parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    tree_sitter = None

try:
    import tree_sitter_python
    TREE_SITTER_PYTHON_AVAILABLE = True
except ImportError:
    TREE_SITTER_PYTHON_AVAILABLE = False
    tree_sitter_python = None


class TreeSitterParser:
    """Tree-sitter AST 解析器"""

    def __init__(self):
        self.parser = None
        self._initialized = False
        self._init_parser()

    def _init_parser(self):
        """初始化 Tree-sitter 解析器"""
        if not TREE_SITTER_AVAILABLE or not TREE_SITTER_PYTHON_AVAILABLE:
            self._initialized = False
            return

        try:
            from tree_sitter_python import language

            # 创建 Language 对象（从 PyCapsule）
            lang_obj = Language(language())

            # 创建解析器
            self.parser = Parser(lang_obj)
            self._initialized = True
        except Exception as e:
            self._initialized = False

    @property
    def is_available(self) -> bool:
        """检查 Tree-sitter 是否可用"""
        return self._initialized and TREE_SITTER_AVAILABLE and TREE_SITTER_PYTHON_AVAILABLE

    def parse(self, code: str) -> Optional["tree_sitter.Tree"]:
        """
        解析 Python 代码为 AST

        Args:
            code: Python 代码字符串

        Returns:
            Tree-sitter Tree 对象，如果解析失败返回 None
        """
        if not self.is_available:
            return None

        try:
            tree = self.parser.parse(bytes(code, "utf8"))
            return tree
        except Exception as e:
            return None

    def extract_formulas(self, code: str) -> List["z3.BoolRef"]:
        """
        从 Python 代码中提取 Z3 逻辑公式

        提取内容：
        - 条件表达式 (if/while/assert)
        - 比较运算
        - 布尔运算
        - 循环不变式

        Args:
            code: Python 代码

        Returns:
            Z3 公式列表
        """
        formulas = []

        if not self.is_available:
            return formulas

        tree = self.parse(code)
        if tree is None:
            return formulas

        # 遍历 AST 提取公式
        self._extract_from_node(tree.root_node, formulas)

        return formulas

    def _extract_from_node(self, node, formulas: List):
        """递归遍历 AST 节点提取公式"""
        if node is None:
            return

        # 处理不同类型的节点
        node_type = node.type

        if node_type == "if_statement":
            # 只递归处理子节点，comparison_operator 会提取条件
            for child in node.children:
                if child.type in ("block", "else"):
                    self._extract_from_node(child, formulas)

        elif node_type == "while_statement":
            # 提取 while 条件
            condition = node.child_by_field_name("condition")
            if condition:
                # The condition is a comparison_operator, not comparison
                formula = self._comparison_to_formula(condition)
                if formula is None:
                    # Try as generic condition
                    formula = self._node_to_formula(condition)
                if formula is not None:
                    formulas.append(formula)

        elif node_type == "assert_statement":
            # 提取 assert 条件
            condition = node.child_by_field_name("message")
            if condition:
                formula = self._node_to_formula(condition)
                if formula is not None:
                    formulas.append(formula)

        elif node_type == "comparison":
            # 提取比较表达式
            formula = self._comparison_to_formula(node)
            if formula is not None:
                formulas.append(formula)

        elif node_type == "comparison_operator":
            # 提取比较运算符表达式
            formula = self._comparison_to_formula(node)
            if formula is not None:
                formulas.append(formula)

        elif node_type == "boolean_operator":
            # 提取布尔运算符
            formula = self._boolean_to_formula(node)
            if formula is not None:
                formulas.append(formula)

        # 递归处理子节点
        for child in node.children:
            self._extract_from_node(child, formulas)

    def _node_to_formula(self, node) -> Optional["z3.BoolRef"]:
        """将 AST 节点转换为 Z3 公式"""
        if node is None:
            return None

        try:
            from z3 import Bool, Int

            # 获取节点文本
            text = node.text.decode("utf8") if hasattr(node.text, "decode") else str(node.text)

            # 处理比较表达式
            if node.type == "comparison":
                return self._comparison_to_formula(node)

            # 处理标识符 -> 创建布尔变量
            if node.type == "identifier":
                return Bool(text)

            # 处理数字 -> 转换为整数
            if node.type in ("integer", "decimal_integer"):
                try:
                    val = int(text)
                    return Int(val) >= 0  # 恒真约束
                except:
                    return None

            return None

        except Exception:
            return None

    def _comparison_to_formula(self, node) -> Optional["z3.BoolRef"]:
        """将比较表达式转换为 Z3 公式"""
        try:
            from z3 import Bool, Int, Real

            # Handle both "comparison" and "comparison_operator" node types
            if node.type not in ("comparison", "comparison_operator"):
                return None

            # 获取比较操作符和操作数
            left = node.child_by_field_name("left")
            right = node.child_by_field_name("right")

            # For comparison_operator, fields don't exist - use positional children
            if node.type == "comparison_operator":
                children = node.children
                if len(children) >= 3:
                    left = children[0]
                    operator_node = children[1]
                    right = children[2]
                    operator = operator_node.type if operator_node else None
                else:
                    return None
            elif left is None or right is None:
                return None
            else:
                # 获取操作符
                operator = None
                for child in node.children:
                    if child.type in ("==", "!=", "<", "<=", ">", ">=", "in", "not_in"):
                        operator = child.type
                        break

            if operator is None or left is None or right is None:
                return None

            # 获取操作数的文本
            left_text = left.text.decode("utf8") if hasattr(left.text, "decode") else ""
            right_text = right.text.decode("utf8") if hasattr(right.text, "decode") else ""

            # 创建 Z3 变量
            try:
                left_val = int(left_text)
                left_expr = Int(left_val)
            except:
                left_expr = Int(left_text) if left_text else None

            try:
                right_val = int(right_text)
                right_expr = Int(right_val)
            except:
                right_expr = Int(right_text) if right_text else None

            if left_expr is None or right_expr is None:
                return None

            # 根据操作符返回对应的 Z3 表达式
            op_map = {
                "==": left_expr == right_expr,
                "!=": left_expr != right_expr,
                "<": left_expr < right_expr,
                "<=": left_expr <= right_expr,
                ">": left_expr > right_expr,
                ">=": left_expr >= right_expr,
            }

            return op_map.get(operator)

        except Exception:
            return None

    def _boolean_to_formula(self, node) -> Optional["z3.BoolRef"]:
        """将布尔表达式转换为 Z3 公式"""
        try:
            from z3 import And, Or, Not

            if node.type != "boolean_operator":
                return None

            # 获取操作符和操作数
            op = None
            left = None
            right = None

            for child in node.children:
                if child.type in ("and", "or", "not"):
                    op = child.type
                elif child.type == "left":
                    left = child
                elif child.type == "right":
                    right = child

            if op is None or left is None or right is None:
                return None

            left_formula = self._node_to_formula(left)
            right_formula = self._node_to_formula(right)

            if left_formula is None and right_formula is None:
                return None

            if op == "and":
                return And(left_formula, right_formula)
            elif op == "or":
                return Or(left_formula, right_formula)
            elif op == "not":
                return Not(left_formula) if left_formula else None

            return None

        except Exception:
            return None

    def extract_branch_conditions(self, code: str) -> List[Dict[str, Any]]:
        """
        提取代码中的分支条件

        Args:
            code: Python 代码

        Returns:
            分支条件列表，每项包含：
            - type: 条件类型 (if/while/assert)
            - condition: 条件表达式文本
            - line: 行号
        """
        conditions = []

        if not self.is_available:
            return conditions

        tree = self.parse(code)
        if tree is None:
            return conditions

        self._collect_conditions(tree.root_node, conditions)

        return conditions

    def _collect_conditions(self, node, conditions: List):
        """递归收集条件表达式"""
        if node is None:
            return

        node_type = node.type

        if node_type == "if_statement":
            condition_node = node.child_by_field_name("condition")
            if condition_node:
                conditions.append({
                    "type": "if",
                    "condition": condition_node.text.decode("utf8") if hasattr(condition_node.text, "decode") else str(condition_node.text),
                    "line": condition_node.start_point[0] + 1
                })

        elif node_type == "while_statement":
            condition_node = node.child_by_field_name("condition")
            if condition_node:
                conditions.append({
                    "type": "while",
                    "condition": condition_node.text.decode("utf8") if hasattr(condition_node.text, "decode") else str(condition_node.text),
                    "line": condition_node.start_point[0] + 1
                })

        elif node_type == "assert_statement":
            # assert 语句的条件在第一个子节点
            if node.children:
                conditions.append({
                    "type": "assert",
                    "condition": node.children[0].text.decode("utf8") if hasattr(node.children[0].text, "decode") else str(node.children[0].text),
                    "line": node.start_point[0] + 1
                })

        # 递归处理子节点
        for child in node.children:
            self._collect_conditions(child, conditions)


def create_parser() -> Optional[TreeSitterParser]:
    """创建 Tree-sitter 解析器实例"""
    parser = TreeSitterParser()
    if parser.is_available:
        return parser
    return None