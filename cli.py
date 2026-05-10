"""
AetherHub CLI - 自主认知技能系统命令行工具
"""
import sys
import os
from typing import Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# 全局配置
CONFIG = {
    "model": os.getenv("CODEX_MODEL", "gpt-4o"),
    "z3_timeout": int(os.getenv("Z3_TIMEOUT", "30")),
    "wasm_memory_limit": int(os.getenv("WASM_MEMORY_LIMIT", "16")),
    "wasm_time_limit": int(os.getenv("WASM_TIME_LIMIT", "5000")),
}


@click.group()
def main():
    """AetherHub - 自主认知技能系统 CLI"""
    pass


@main.command()
@click.argument("intent")
@click.option("-v", "--verbose", is_flag=True, help="详细输出")
@click.option("--no-verify", is_flag=True, help="跳过 Z3 验证")
@click.option("--no-exec", is_flag=True, help="跳过执行")
def run(intent, verbose, no_verify, no_exec):
    """
    运行 ISMP 流水线，处理技能意图并生成代码

    Example:
        aetherhub run "将 /data/users.csv 中年龄大于 18 的用户导出到 /tmp/adults.csv"
    """
    console.print(Panel.fit(
        f"[bold cyan]AetherHub ISMP Pipeline[/bold cyan]\n"
        f"Intent: {intent}",
        border_style="cyan"
    ))

    try:
        from aetherhub.ismp.protocol import ISMPProtocol
        from aetherhub.codex.engine import CodexEngine
        from aetherhub.verification.z3_verifier import Z3Verifier
        from aetherhub.execution.wasmtime import WasmtimeSandbox
    except ImportError as e:
        console.print(f"[red]Error: Failed to import AetherHub modules: {e}[/red]")
        console.print("[yellow]Hint: 确认已安装 aetherhub (pip install -e .)[/yellow]")
        raise SystemExit(1)

    # 初始化组件
    codex = CodexEngine(model=CONFIG["model"])
    z3 = Z3Verifier(timeout=CONFIG["z3_timeout"])
    wasm = WasmtimeSandbox(
        memory_limit_mb=CONFIG["wasm_memory_limit"],
        time_limit_ms=CONFIG["wasm_time_limit"]
    )
    ismp = ISMPProtocol(codex, None, z3)

    # Step 1: ISMP 处理
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("[cyan]处理意图...", total=None)
        artifact = ismp.process(intent)

    console.print(f"[green]✓[/green] 技能产物已生成: {artifact['artifact_id']}")
    if verbose:
        console.print(f"  原子技能: {', '.join(artifact['atomic_skills'])}")
        console.print(f"  资源类型: {artifact['constraints']['resource_type']}")
        console.print(f"  代码行数: {len(artifact['code'].split(chr(10)))}")

    # Step 2: Z3 验证
    if no_verify:
        console.print("[yellow]跳过验证[/yellow]")
    else:
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            progress.add_task("[cyan]验证代码安全性...", total=None)
            verification_result = z3.verify(
                artifact['code'],
                artifact['constraints']['rules']
            )

        status_color = "green" if verification_result['status'] == "verified" else "red"
        console.print(f"[{status_color}]✓[/] 验证状态: {verification_result['status']}")
        console.print(f"  结果: {verification_result['result']}")
        if verbose:
            console.print(f"  规则数: {len(artifact['constraints']['rules'])}")

    # Step 3: 执行代码
    if no_exec:
        console.print("[yellow]跳过执行[/yellow]")
    else:
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            progress.add_task("[cyan]执行代码...", total=None)
            execution_result = wasm.execute(artifact['code'])

        exec_color = "green" if execution_result['status'] == "success" else "red"
        console.print(f"[{exec_color}]✓[/] 执行状态: {execution_result['status']}")
        console.print(f"  执行时间: {execution_result['execution_time_ms']}ms")
        console.print(f"  内存使用: {execution_result['memory_usage_mb']}MB")

    console.print("\n[bold green]处理完成![/bold green]")


@main.command()
@click.argument("code_file")
@click.option("-r", "--rules", help="额外规则（逗号分隔）")
def verify(code_file, rules):
    """
    验证代码文件安全性（不执行）

    Example:
        aetherhub verify output.py --rules "禁止访问 /etc,禁止访问 /usr"
    """
    try:
        with open(code_file, "r") as f:
            code = f.read()
    except FileNotFoundError:
        console.print(f"[red]Error: 文件不存在: {code_file}[/red]")
        raise SystemExit(1)

    from aetherhub.verification.z3_verifier import Z3Verifier

    z3 = Z3Verifier(timeout=CONFIG["z3_timeout"])

    default_rules = [
        "禁止访问 /etc", "禁止访问 /usr", "禁止访问 /sys",
        "禁止访问 /dev", "禁止访问 /proc", "禁止访问 /var/log",
        "禁止访问 /root", "文件大小不超过 100MB"
    ]

    if rules:
        default_rules.extend(rules.split(","))

    console.print(f"[cyan]验证文件: {code_file}[/cyan]")
    console.print(f"[cyan]规则数量: {len(default_rules)}[/cyan]\n")

    result = z3.verify(code, default_rules)

    status_color = "green" if result['status'] == "verified" else "red"
    console.print(f"[{status_color}]状态: {result['status']}[/{status_color}]")
    console.print(f"结果: {result['result']}")

    if result.get('violations'):
        console.print("\n[red]违规项:[/red]")
        for v in result['violations']:
            console.print(f"  - {v}")


@main.command()
@click.argument("code")
@click.option("-m", "--memory", default=16, help="内存限制 (MB)")
@click.option("-t", "--time", default=5000, help="时间限制 (ms)")
def execute(code, memory, time):
    """
    在 Wasm 沙箱中执行代码（安全模式）

    Example:
        aetherhub execute 'print("hello")' --memory 8 --time 3000
    """
    # 如果是文件，读取内容
    if os.path.isfile(code):
        with open(code, "r") as f:
            code = f.read()

    from aetherhub.execution.wasmtime import WasmtimeSandbox

    wasm = WasmtimeSandbox(memory_limit_mb=memory, time_limit_ms=time)

    console.print(f"[cyan]执行代码 (memory={memory}MB, time={time}ms)...[/cyan]\n")

    result = wasm.execute(code)

    status_color = "green" if result['status'] == "success" else "red"
    console.print(f"[{status_color}]状态: {result['status']}[/{status_color}]")
    console.print(f"输出: {result.get('output', 'N/A')}")
    console.print(f"执行时间: {result['execution_time_ms']}ms")
    console.print(f"内存使用: {result['memory_usage_mb']}MB")

    if result.get('blocked'):
        console.print("[yellow]代码被沙箱拦截[/yellow]")


@main.command()
def info():
    """显示 AetherHub 系统信息"""
    console.print(Panel.fit(
        "[bold cyan]AetherHub 系统信息[/bold cyan]\n"
        f"版本: 1.0.0\n"
        f"Codex Model: {CONFIG['model']}\n"
        f"Z3 Timeout: {CONFIG['z3_timeout']}s\n"
        f"Wasm Memory Limit: {CONFIG['wasm_memory_limit']}MB\n"
        f"Wasm Time Limit: {CONFIG['wasm_time_limit']}ms",
        border_style="cyan"
    ))


@main.command()
def version():
    """显示版本信息"""
    console.print("AetherHub CLI v1.0.0")


if __name__ == "__main__":
    main()