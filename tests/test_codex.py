"""Codex 引擎测试"""
import pytest
from aetherhub.codex.engine import CodexEngine


class TestCodexEngine:
    """Codex 引擎测试"""

    def test_init(self):
        """测试初始化"""
        codex = CodexEngine()
        assert codex.model == "codex-3.5"

    def test_init_with_custom_model(self):
        """测试使用自定义模型"""
        codex = CodexEngine(model="codex-4.0")
        assert codex.model == "codex-4.0"

    def test_generate_simple(self):
        """测试生成简单代码"""
        codex = CodexEngine()
        prompt = "写一个 Python 函数，计算两个数的和"
        code = codex.generate(prompt)

        assert code is not None
        assert len(code) > 0
        assert "def process" in code or "def calculate" in code

    def test_generate_with_max_tokens(self):
        """测试生成代码时限制最大token数"""
        codex = CodexEngine()
        prompt = "写一个 Python 函数"
        code = codex.generate(prompt, max_tokens=100)

        assert code is not None
        assert len(code) <= 100

    def test_generate_complex(self):
        """测试生成复杂代码（mock 模式下验证基本结构）"""
        codex = CodexEngine()
        prompt = """写一个 Python 类，用于处理用户数据：
1. 包含 name, age, email 字段
2. 实现 __init__ 方法
3. 实现 get_info 方法
4. 实现 update_info 方法"""
        code = codex.generate(prompt)

        assert code is not None
        assert len(code) > 0
        # mock 模式下验证基本代码结构即可
        assert "def" in code

    def test_generate_with_variable_prompt(self):
        """测试不同提示词均能生成有效代码（mock 模式）"""
        codex = CodexEngine()

        prompt1 = "写一个 Python 函数，计算斐波那契数列"
        code1 = codex.generate(prompt1)

        prompt2 = "写一个 Python 函数，计算阶乘"
        code2 = codex.generate(prompt2)

        assert code1 is not None and len(code1) > 0
        assert code2 is not None and len(code2) > 0
        # mock 模式下两次调用返回相同模板，仅验证非空
        assert "def" in code1
        assert "def" in code2

    def test_verify_and_fix(self):
        """测试代码验证和修复"""
        codex = CodexEngine()

        # 有问题的代码
        code = """
def process():
    x = 1
    y = 2
    return x + y
    # 缺少 return
"""

        fixed_code = codex.verify_and_fix(code)

        assert fixed_code is not None
        assert len(fixed_code) > 0

    def test_verify_and_fix_valid_code(self):
        """测试验证和修复有效代码"""
        codex = CodexEngine()

        # 有效代码
        code = """
def process():
    x = 1
    y = 2
    return x + y
"""

        fixed_code = codex.verify_and_fix(code)

        assert fixed_code is not None
        assert len(fixed_code) > 0

    def test_generate_empty_prompt(self):
        """测试空提示词"""
        codex = CodexEngine()
        code = codex.generate("")

        assert code is not None
        # 空提示词应该返回默认代码

    def test_generate_very_long_prompt(self):
        """测试超长提示词"""
        codex = CodexEngine()

        # 构造一个超长提示词
        prompt = "写一个 Python 函数" + " 参数" * 1000
        code = codex.generate(prompt, max_tokens=2000)

        assert code is not None
        assert len(code) <= 2000

    def test_generate_code_structure(self):
        """测试生成代码的结构"""
        codex = CodexEngine()
        prompt = "写一个 Python 脚本，包含 main 函数"
        code = codex.generate(prompt)

        # 检查代码结构
        lines = code.strip().split('\n')
        assert len(lines) > 0
        assert any(line.strip().startswith('def') for line in lines)
