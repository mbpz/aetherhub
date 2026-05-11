"""
AetherHub CLI - 自主认知技能系统命令行工具
"""
import json
import os
import sys
import time
import http.server
import threading
import urllib.parse
from pathlib import Path
from datetime import datetime
from typing import Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import click
import httpx
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

# Credentials management
CREDENTIALS_FILE = Path.home() / ".aetherhub" / "credentials"

def load_credentials():
    if not CREDENTIALS_FILE.exists():
        return None
    try:
        with open(CREDENTIALS_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None

def save_credentials(data):
    CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    CREDENTIALS_FILE.write_text(json.dumps(data, indent=2))
    os.chmod(CREDENTIALS_FILE, 0o600)

def clear_credentials():
    if CREDENTIALS_FILE.exists():
        CREDENTIALS_FILE.unlink()

def get_auth_header():
    creds = load_credentials()
    if not creds:
        return None
    return {"Authorization": f"Bearer {creds['access_token']}"}


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


@main.command()
def login():
    """GitHub OAuth 登录（设备码流程）"""
    console.print("[cyan]启动 GitHub OAuth 设备码登录...[/cyan]")

    auth_code = {"code": None}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            if "code" in params:
                auth_code["code"] = params["code"][0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write("<h1>登录成功！可以关闭此窗口。</h1>".encode("utf-8"))
            else:
                self.send_response(400)
                self.end_headers()

        def log_message(self, format, *args):
            pass

    server = http.server.HTTPServer(("localhost", 8765), Handler)
    thread = threading.Thread(target=lambda: server.handle_request())
    thread.start()

    client_id = os.getenv("GITHUB_CLIENT_ID", "Ov23liQI8mK4aSgO4p8K")
    device_url = f"https://github.com/login/device/code?client_id={client_id}"
    console.print(f"[yellow]请访问: {device_url}[/yellow]")
    console.print("[yellow]在页面上输入设备码完成授权[/yellow]")

    # Wait for auth code (simulated - actual implementation would use GitHub API)
    console.print("[yellow]等待授权...(按 Ctrl+C 取消)[/yellow]")
    time.sleep(3)

    # Mock token for demo purposes
    save_credentials({
        "access_token": "mock_token_" + str(int(time.time())),
        "expires_at": int(time.time()) + 86400 * 30,
        "user": {
            "id": 1,
            "username": "demo_user",
            "avatar_url": "https://avatars.githubusercontent.com/u/1",
        },
    })

    console.print("[green]登录成功！[/green]")
    console.print(f"凭证已保存到: {CREDENTIALS_FILE}")


@main.command()
def logout():
    """清除本地凭证"""
    clear_credentials()
    console.print("[green]已退出登录[/green]")


@main.command()
def status():
    """显示当前登录状态"""
    creds = load_credentials()
    if not creds:
        console.print("[yellow]未登录，请运行: aetherhub login[/yellow]")
        return
    exp = datetime.fromtimestamp(creds['expires_at'])
    console.print(f"[green]已登录: {creds['user']['username']}[/green]")
    console.print(f"Token 过期时间: {exp}")


@main.command()
@click.argument("path", type=click.Path(exists=True))
def upload(path):
    """上传本地技能目录到市场"""
    skill_path = Path(path)

    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        console.print("[red]未找到 SKILL.md 文件[/red]")
        raise click.Abort()

    with open(skill_md) as f:
        content = f.read()

    allowed_exts = {".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml"}
    files = []
    for f in skill_path.iterdir():
        if f.is_file() and f.suffix in allowed_exts:
            files.append(f)

    console.print(f"[cyan]上传技能: {skill_path.name}[/cyan]")
    console.print(f"[cyan]文件数: {len(files)}[/cyan]")

    API_BASE = os.getenv("AETHERHUB_API_URL", "http://localhost:8000/api")

    headers = get_auth_header()
    if not headers:
        console.print("[red]未登录，请运行: aetherhub login[/red]")
        raise click.Abort()
    headers["Content-Type"] = "application/json"

    import httpx
    with httpx.Client() as client:
        resp = client.post(
            f"{API_BASE}/skills",
            json={
                "name": skill_path.name,
                "description": content.split("\n")[0][:200],
                "skill_md": content,
            },
            headers=headers,
        )
        if resp.status_code == 401:
            console.print("[red]认证失败，请重新登录: aetherhub login[/red]")
            raise click.Abort()
        if resp.status_code not in (200, 201):
            console.print(f"[red]创建技能失败: {resp.text}[/red]")
            raise click.Abort()

        skill = resp.json()
        console.print(f"[green]技能创建成功: {skill['id']}[/green]")

        for f in files:
            with open(f, "rb") as fp:
                files_data = {"file": (f.name, fp.read())}
                file_resp = client.post(
                    f"{API_BASE}/skills/{skill['id']}/files",
                    files=files_data,
                    headers={"Authorization": headers["Authorization"]},
                )
                if file_resp.status_code == 200:
                    console.print(f"  [green]+[/green] {f.name}")
                else:
                    console.print(f"  [red]-[/red] {f.name}")

    console.print("[green]上传完成![/green]")


@main.command()
def publish():
    """在当前目录发布技能（发现 SKILL.md）"""
    ctx = click.get_current_context()
    skill_path = Path(".")
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        console.print("[red]未找到 SKILL.md 文件，请确保在技能目录内运行[/red]")
        raise click.Abort()
    ctx.invoke(upload, path=str(skill_path.absolute()))


@main.command()
@click.argument("name")
@click.option("--version", "-v", default=None, help="指定版本")
def install(name, version):
    """从市场下载技能到本地（默认最新版本）"""
    import httpx
    API_BASE = os.getenv("AETHERHUB_API_URL", "http://localhost:8000/api")

    headers = get_auth_header()
    if not headers:
        console.print("[red]未登录，请运行: aetherhub login[/red]")
        raise typer.Exit(1)

    with httpx.Client() as client:
        search_resp = client.get(
            f"{API_BASE}/skills",
            params={"q": name, "limit": 1},
            headers=headers,
        )
        if search_resp.status_code == 401:
            console.print("[red]认证失败，请重新登录: aetherhub login[/red]")
            raise typer.Exit(1)

        skills = search_resp.json().get("skills", [])
        if not skills:
            console.print(f"[red]未找到技能: {name}[/red]")
            raise typer.Exit(1)

        skill = skills[0]
        skill_id = skill["id"]

        if version:
            ver_resp = client.get(
                f"{API_BASE}/skills/{skill_id}/versions/{version}",
                headers=headers,
            )
            if ver_resp.status_code != 200:
                console.print(f"[red]版本不存在: {version}[/red]")
                raise typer.Exit(1)
            ver_data = ver_resp.json()
        else:
            versions_resp = client.get(
                f"{API_BASE}/skills/{skill_id}/versions",
                headers=headers,
            )
            versions = versions_resp.json().get("versions", [])
            if not versions:
                console.print("[red]该技能没有版本记录[/red]")
                raise typer.Exit(1)
            ver_data = versions[0]
            version = ver_data["version"]

        console.print(f"[cyan]安装技能: {name} v{version}[/cyan]")

        install_dir = Path.home() / ".aetherhub" / "skills" / name
        install_dir.mkdir(parents=True, exist_ok=True)

        skill_data = client.get(
            f"{API_BASE}/skills/{skill_id}",
            headers=headers,
        ).json()

        for f in skill_data.get("files", []):
            file_resp = client.get(
                f"{API_BASE}/skills/{skill_id}/files/{f['filename']}",
                headers=headers,
            )
            if file_resp.status_code == 200:
                file_path = install_dir / f["filename"]
                file_path.write_bytes(file_resp.content)
                console.print(f"  [green]+[/green] {f['filename']}")

        console.print(f"[green]安装完成: {install_dir}[/green]")


@main.command(name="list")
def list_installed():
    """列出已安装到本地的技能"""
    skills_dir = Path.home() / ".aetherhub" / "skills"
    if not skills_dir.exists():
        console.print("[yellow]暂无已安装技能[/yellow]")
        return

    for skill_dir in skills_dir.iterdir():
        if skill_dir.is_dir():
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                console.print(f"[cyan]- {skill_dir.name}[/cyan]")
            else:
                console.print(f"[dim]- {skill_dir.name} (无 SKILL.md)[/dim]")


@main.command()
@click.argument("query")
@click.option("--limit", "-n", default=10, help="结果数量")
def search(query, limit):
    """搜索市场技能"""
    import httpx
    API_BASE = os.getenv("AETHERHUB_API_URL", "http://localhost:8000/api")

    headers = get_auth_header()
    if not headers:
        console.print("[red]未登录，请运行: aetherhub login[/red]")
        raise typer.Exit(1)

    with httpx.Client() as client:
        resp = client.get(
            f"{API_BASE}/skills",
            params={"q": query, "limit": limit},
            headers=headers,
        )

    if resp.status_code == 401:
        console.print("[red]认证失败，请重新登录: aetherhub login[/red]")
        raise typer.Exit(1)

    data = resp.json()
    skills = data.get("skills", [])

    if not skills:
        console.print("[yellow]未找到匹配技能[/yellow]")
        return

    console.print(f"[cyan]找到 {len(skills)} 个技能:[/cyan]")
    for s in skills:
        console.print(f"  [green]{s['name']}[/green] - {s.get('description', '')[:60]}")


if __name__ == "__main__":
    main()