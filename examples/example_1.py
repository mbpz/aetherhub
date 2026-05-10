"""Example 1: 意图 → 技能产物完整流程"""
from aetherhub.ismp.protocol import ISMPProtocol
from aetherhub.codex.engine import CodexEngine
from aetherhub.verification.z3_verifier import Z3Verifier
from aetherhub.execution.wasmtime import WasmtimeSandbox


def demo():
    """演示完整的意图处理流程"""
    print("=" * 60)
    print("AetherHub 意图 → 技能产物演示")
    print("=" * 60)

    # 初始化组件
    print("\n[1] 初始化组件...")
    codex = CodexEngine()
    z3 = Z3Verifier(timeout=10)
    wasm = WasmtimeSandbox(memory_limit_mb=16, time_limit_ms=5000)
    ismp = ISMPProtocol(codex, None, z3)
    print("    ✓ ISMPProtocol")
    print("    ✓ CodexEngine")
    print("    ✓ Z3Verifier")
    print("    ✓ WasmtimeSandbox")

    # 处理用户意图
    print("\n[2] 处理用户意图...")
    intent = "将 /data/users.csv 中年龄大于 18 的用户导出到 /tmp/adults.csv"
    print(f"    意图: {intent}")

    artifact = ismp.process(intent)

    print("\n[3] 生成结果:")
    print(f"    artifact_id: {artifact['artifact_id']}")
    print(f"    意图向量: {artifact['intent_vector']}")
    print(f"    原子技能: {artifact['atomic_skills']}")
    print(f"    代码:\n{artifact['code']}")

    # 验证代码安全性
    print("\n[4] Z3 形式化验证...")
    constraints = artifact['constraints']['rules']
    verification = z3.verify(artifact['code'], constraints)
    print(f"    状态: {verification['status']}")
    print(f"    结果: {verification['result']}")
    if verification['status'] == 'verified':
        print("    ✓ 代码通过安全验证")
    else:
        print(f"    ✗ 验证失败: {verification.get('counterexample', '')}")

    # 执行代码（模拟模式）
    print("\n[5] Wasm 执行...")
    exec_result = wasm.execute(artifact['code'])
    print(f"    状态: {exec_result['status']}")
    print(f"    执行时间: {exec_result['execution_time_ms']}ms")
    print(f"    内存使用: {exec_result['memory_usage_mb']}MB")

    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    demo()