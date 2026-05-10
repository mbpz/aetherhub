"""Example 2: Z3 形式化验证"""
from aetherhub.verification.z3_verifier import Z3Verifier
from aetherhub.verification.tree_sitter_parser import code_to_ast, ast_to_z3_formula, extract_all_constraints


def demo_z3_verification():
    """演示 Z3 形式化验证"""
    print("=" * 60)
    print("Z3 形式化验证演示")
    print("=" * 60)

    # 示例代码
    code_samples = [
        {
            "name": "安全代码 - 路径检查",
            "code": '''
def safe_read_csv(filepath):
    forbidden = ["/etc", "/usr", "/sys"]
    for path in forbidden:
        if filepath.startswith(path):
            raise ValueError("禁止访问")
    return "OK"
'''
        },
        {
            "name": "危险代码 - 系统目录访问",
            "code": '''
def read_etc_file():
    with open("/etc/passwd", "r") as f:
        return f.read()
'''
        },
        {
            "name": "边界情况 - 循环限制",
            "code": '''
def process_large_data(n):
    count = 0
    for i in range(n):
        if i > 1000:
            break
        count += 1
    return count
'''
        },
    ]

    z3 = Z3Verifier(timeout=10)

    for sample in code_samples:
        print(f"\n[测试] {sample['name']}")
        print(f"代码:\n{sample['code']}")

        # 提取约束
        try:
            constraints = extract_all_constraints(sample['code'])
            print(f"提取到 {len(constraints)} 个约束")
        except Exception as e:
            print(f"约束提取失败: {e}")
            constraints = []

        # 验证
        verification = z3.verify(sample['code'], ["禁止访问 /etc", "禁止访问 /usr"])

        print(f"验证结果: {verification['status']}")
        if verification['status'] == 'verified':
            print("  ✓ 通过")
        else:
            print(f"  ✗ 失败: {verification.get('counterexample', 'N/A')}")

    print("\n" + "=" * 60)


def demo_tree_sitter():
    """演示 Tree-sitter AST 解析"""
    print("\n[Tree-sitter 演示]")
    print("-" * 40)

    code = '''
def add(a, b):
    return a + b

x = 10
y = 20
result = x + y
'''

    try:
        tree = code_to_ast(code)
        print(f"AST 根节点类型: {tree.type}")
        print(f"AST 文本长度: {len(tree.text)} 字符")

        formula = ast_to_z3_formula(tree)
        print(f"Z3 公式: {formula}")
    except Exception as e:
        print(f"Tree-sitter 解析失败: {e}")

    print("-" * 40)


if __name__ == "__main__":
    demo_z3_verification()
    demo_tree_sitter()