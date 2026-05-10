"""Example 3: Wasm 执行沙箱"""
from aetherhub.execution.wasmtime import WasmtimeSandbox
from aetherhub.execution.sandbox import Sandbox, SandboxConfig, create_sandbox


def demo_wasm_execution():
    """演示 Wasm 执行沙箱"""
    print("=" * 60)
    print("Wasm 执行沙箱演示")
    print("=" * 60)

    # 创建沙箱
    config = SandboxConfig(
        memory_limit_mb=16,
        time_limit_ms=5000,
        allowed_paths=["/tmp", "/var/tmp"],
        forbidden_paths=["/etc", "/usr", "/sys", "/dev", "/proc", "/var/log", "/root"]
    )
    sandbox = Sandbox(config)

    # 测试代码
    code_samples = [
        {
            "name": "安全代码",
            "code": '''
def process_data(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result
''',
        },
        {
            "name": "危险代码 - 系统目录访问",
            "code": '''
def read_system_file():
    with open("/etc/passwd", "r") as f:
        return f.read()
''',
        },
        {
            "name": "危险代码 - exec",
            "code": '''
def dangerous():
    exec("print('hello')")
''',
        },
    ]

    for sample in code_samples:
        print(f"\n[测试] {sample['name']}")

        # 验证代码
        validation = sandbox.validate_code(sample["code"])
        print(f"  验证结果: {'通过' if validation['valid'] else '拒绝'}")
        if not validation["valid"]:
            print(f"  违规: {validation['violations']}")
            continue

        # 执行代码
        wasm = WasmtimeSandbox(memory_limit_mb=16, time_limit_ms=5000)
        result = wasm.execute(sample["code"])

        print(f"  执行状态: {result['status']}")
        print(f"  执行时间: {result['execution_time_ms']}ms")
        print(f"  内存使用: {result['memory_usage_mb']}MB")

    print("\n" + "=" * 60)


def demo_sandbox_config():
    """演示沙箱配置"""
    print("\n[沙箱配置演示]")
    print("-" * 40)

    configs = [
        {"name": "宽松模式", "memory_limit_mb": 64, "time_limit_ms": 30000},
        {"name": "严格模式", "memory_limit_mb": 8, "time_limit_ms": 1000},
        {"name": "默认模式", "memory_limit_mb": 16, "time_limit_ms": 5000},
    ]

    for cfg in configs:
        sandbox = create_sandbox(cfg)
        print(f"  {cfg['name']}:")
        print(f"    内存限制: {sandbox.config.memory_limit_mb}MB")
        print(f"    时间限制: {sandbox.config.time_limit_ms}ms")
        print(f"    允许路径: {sandbox.config.allowed_paths}")
        print(f"    禁止路径: {sandbox.config.forbidden_paths[:3]}...")

    print("-" * 40)


if __name__ == "__main__":
    demo_wasm_execution()
    demo_sandbox_config()