"""主程序"""
import sys
from aetherhub.ismp.protocol import ISMPProtocol
from aetherhub.codex.engine import CodexEngine
from aetherhub.verification.z3_verifier import Z3Verifier
from aetherhub.execution.wasmtime import WasmtimeSandbox
from aetherhub.utils.report import ReportGenerator


def main():
    """主函数"""
    print("🚀 AetherHub 启动中...")

    # 初始化组件
    codex = CodexEngine(model="codex-3.5")
    z3 = Z3Verifier(timeout=30)
    wasm = WasmtimeSandbox(memory_limit_mb=16, time_limit_ms=5000)

    # 创建 ISMP 协议实例
    ismp = ISMPProtocol(codex, None, z3)

    # 创建报告生成器
    report_gen = ReportGenerator()

    # 示例：处理用户意图
    intent = "将 /data/users.csv 中的年龄大于 18 的用户导出到 /tmp/adults.csv"

    print(f"\n📝 处理意图: {intent}\n")

    # Step 1: ISMP 协议处理
    artifact = ismp.process(intent)

    print(f"✅ 技能产物已生成: {artifact['artifact_id']}")
    print(f"   原子技能: {', '.join(artifact['atomic_skills'])}")
    print(f"   资源类型: {artifact['constraints']['resource_type']}")
    print(f"   代码行数: {len(artifact['code'].split(chr(10)))}")

    # Step 2: 代码验证
    print("\n🔍 验证代码安全性...")
    verification_result = z3.verify(
        artifact['code'],
        artifact['constraints']['rules']
    )

    print(f"   状态: {verification_result['status']}")
    print(f"   结果: {verification_result['result']}")
    print(f"   规则数: {len(artifact['constraints']['rules'])}")

    artifact['metadata']['verification_result'] = verification_result['status']

    # Step 3: 生成报告
    print("\n📄 生成验证报告...")
    report = report_gen.generate(artifact, verification_result)
    print(f"   报告ID: {report['report_id']}")
    print(f"   报告路径: {report['report_path']}")

    # Step 4: 执行代码（模拟）
    print("\n🚀 执行代码...")
    execution_result = wasm.execute(artifact['code'])
    print(f"   状态: {execution_result['status']}")
    print(f"   执行时间: {execution_result['execution_time_ms']}ms")
    print(f"   内存使用: {execution_result['memory_usage_mb']}MB")

    # Step 5: 验证执行结果
    print("\n✅ 验证执行结果...")
    if wasm.verify_execution(execution_result):
        print("   执行结果验证通过")
    else:
        print("   警告: 执行结果超出安全范围")

    print("\n🎉 AetherHub 处理完成!")


if __name__ == "__main__":
    main()
