"""AetherHub 完整功能测试"""
import sys
import os

# 添加 aetherhub 到路径
sys.path.insert(0, '.')

from codex.engine import CodexEngine
from verification.z3_verifier import Z3Verifier
from ismp.protocol import ISMPProtocol
from execution.wasmtime import WasmtimeSandbox


def test_semantic_vectorization():
    """测试语义向量化"""
    print("🧪 测试 1: 语义向量化...")
    codex = CodexEngine()
    z3 = Z3Verifier()
    ismp = ISMPProtocol(codex, None, z3)

    intent = "将 /data/users.csv 导出"
    vector = ismp.semantic_vectorization(intent)

    assert vector["verb"] == "write", f"期望 verb='write'，得到 '{vector['verb']}'"
    assert vector["object"] == "file", f"期望 object='file'，得到 '{vector['object']}'"
    assert vector["target"] == "/data/users.csv", f"期望 target='/data/users.csv'，得到 '{vector['target']}'"

    print("   ✅ 通过")
    return True


def test_capability_mapping():
    """测试能力空间匹配"""
    print("🧪 测试 2: 能力空间匹配...")
    codex = CodexEngine()
    z3 = Z3Verifier()
    ismp = ISMPProtocol(codex, None, z3)

    vector = {"verb": "write", "object": "file", "target": "/tmp/data.txt"}
    skills = ismp.capability_mapping(vector)

    assert "read_file" in skills, f"期望 'read_file' 在技能列表中"
    assert "write_file" in skills, f"期望 'write_file' 在技能列表中"

    print("   ✅ 通过")
    return True


def test_constraint_injection():
    """测试约束注入"""
    print("🧪 测试 3: 约束注入...")
    codex = CodexEngine()
    z3 = Z3Verifier()
    ismp = ISMPProtocol(codex, None, z3)

    vector = {"object": "file", "target": "/etc/passwd"}
    code = "def process(): pass"
    constraints = ismp.dynamic_constraint_injection(vector, code)

    assert "file" in constraints["resource_type"], f"期望 resource_type='file'，得到 '{constraints['resource_type']}'"
    assert len(constraints["rules"]) > 0, f"期望规则数 > 0，得到 {len(constraints['rules'])}"

    print("   ✅ 通过")
    return True


def test_full_process():
    """测试完整流程"""
    print("🧪 测试 4: 完整流程...")
    codex = CodexEngine()
    z3 = Z3Verifier()
    ismp = ISMPProtocol(codex, None, z3)

    intent = "将 /data/users.csv 中的年龄大于 18 的用户导出到 /tmp/adults.csv"
    artifact = ismp.process(intent)

    assert artifact["artifact_id"] is not None, f"期望 artifact_id 不为空"
    assert len(artifact["atomic_skills"]) > 0, f"期望原子技能列表不为空"
    assert artifact["code"] is not None, f"期望代码不为空"
    assert artifact["constraints"]["resource_type"] == "file", f"期望资源类型为 'file'"

    print(f"   ✅ 通过 (artifact_id: {artifact['artifact_id']})")
    return True


def test_z3_verification():
    """测试 Z3 验证"""
    print("🧪 测试 5: Z3 形式化验证...")
    z3 = Z3Verifier(timeout=30)

    code = "def process(): pass"
    constraints = ["禁止访问 /etc", "禁止访问 /usr"]

    result = z3.verify(code, constraints)

    assert result["status"] in ["verified", "failed"], f"期望状态为 'verified' 或 'failed'，得到 '{result['status']}'"
    assert result["rules"] == constraints, f"期望规则与输入一致"

    print(f"   ✅ 通过 (状态: {result['status']})")
    return True


def test_wasm_execution():
    """测试 Wasm 执行沙箱"""
    print("🧪 测试 6: Wasm 执行沙箱...")
    wasm = WasmtimeSandbox(memory_limit_mb=16, time_limit_ms=5000)

    code = "def process(): pass"
    result = wasm.execute(code)

    assert result["status"] in ["success", "error"], f"期望状态为 'success' 或 'error'，得到 '{result['status']}'"
    assert "execution_time_ms" in result, f"期望包含 execution_time_ms"
    assert "memory_usage_mb" in result, f"期望包含 memory_usage_mb"

    print(f"   ✅ 通过 (状态: {result['status']}, 耗时: {result['execution_time_ms']}ms, 内存: {result['memory_usage_mb']}MB)")
    return True


def test_edge_cases():
    """测试边界情况"""
    print("🧪 测试 7: 边界情况...")

    codex = CodexEngine()
    z3 = Z3Verifier()
    ismp = ISMPProtocol(codex, None, z3)

    # 测试空意图
    vector = ismp.semantic_vectorization("")
    assert vector["verb"] == "unknown", f"期望 verb='unknown'，得到 '{vector['verb']}'"

    # 测试无目标意图
    vector = ismp.semantic_vectorization("导出数据")
    assert vector["object"] == "unknown", f"期望 object='unknown'，得到 '{vector['object']}'"

    print("   ✅ 通过")
    return True


def main():
    """运行所有测试"""
    print("=" * 60)
    print("🚀 AetherHub 完整功能测试")
    print("=" * 60)
    print()

    tests = [
        test_semantic_vectorization,
        test_capability_mapping,
        test_constraint_injection,
        test_full_process,
        test_z3_verification,
        test_wasm_execution,
        test_edge_cases
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
                print(f"   ❌ 失败")
        except Exception as e:
            failed += 1
            print(f"   ❌ 错误: {str(e)}")
        print()

    print("=" * 60)
    print(f"📊 测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
