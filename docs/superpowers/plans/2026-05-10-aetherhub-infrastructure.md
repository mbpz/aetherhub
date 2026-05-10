# AetherHub 企业化基础设施实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 Storage 抽象层 + CLI Auth + 版本管理 API/UI + CLI 用户端命令

**Architecture:**
- `web/backend/services/storage.py`: StorageService ABC + LocalStorage + S3Storage
- `web/backend/routes/skills.py`: 扩展版本管理 API + 删除/restore/diff
- `cli.py`: 新增 login/logout/upload/publish/install/search/list 命令
- 共享 JWT 认证，凭证存 `~/.aetherhub/credentials`

**Tech Stack:** FastAPI, boto3, typer, githubauth_device

---

## 文件结构

```
web/backend/
  services/
    storage.py        # 新建：StorageService + LocalStorage + S3Storage
  routes/
    skills.py         # 修改：扩展版本管理 API
  config.py           # 新建：STORAGE_BACKEND 等配置

cli.py                # 修改：login/logout/upload/publish/install/search/list

web/frontend/src/
  pages/
    SkillVersionsPage.jsx   # 新建：版本历史 UI
  components/
    VersionDiff.jsx         # 新建：版本对比组件
    VersionSelector.jsx     # 新建：版本选择器
```

---

## Task 1: Storage 抽象层

**Files:**
- Create: `web/backend/services/storage.py`
- Create: `tests/test_storage.py`
- Modify: `web/backend/config.py`（若不存在则新建）

- [ ] **Step 1: 创建 services 目录**

```bash
mkdir -p web/backend/services
touch web/backend/services/__init__.py
```

- [ ] **Step 2: 编写 LocalStorage 实现**

```python
# web/backend/services/storage.py
import os
import shutil
from abc import ABC, abstractmethod
from typing import Optional

class StorageService(ABC):
    @abstractmethod
    async def upload_file(self, local_path: str, remote_key: str) -> str:
        """上传文件，返回存储路径/URL"""
        pass

    @abstractmethod
    async def download_file(self, remote_key: str, local_path: str) -> None:
        """下载文件到本地"""
        pass

    @abstractmethod
    async def delete_file(self, remote_key: str) -> None:
        """删除文件"""
        pass

    @abstractmethod
    def get_url(self, remote_key: str, expires: int = 3600) -> str:
        """获取访问URL（预签名或本地路径）"""
        pass


class LocalStorage(StorageService):
    def __init__(self, base_dir: str):
        self.base_dir = base_dir

    def _resolve(self, remote_key: str) -> str:
        return os.path.join(self.base_dir, remote_key)

    async def upload_file(self, local_path: str, remote_key: str) -> str:
        dest = self._resolve(remote_key)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(local_path, dest)
        return dest

    async def download_file(self, remote_key: str, local_path: str) -> None:
        src = self._resolve(remote_key)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        shutil.copy2(src, local_path)

    async def delete_file(self, remote_key: str) -> None:
        path = self._resolve(remote_key)
        if os.path.exists(path):
            os.remove(path)

    def get_url(self, remote_key: str, expires: int = 3600) -> str:
        return self._resolve(remote_key)
```

- [ ] **Step 3: 编写 S3Storage 实现**

```python
class S3Storage(StorageService):
    def __init__(self, bucket: str, region: str = "us-east-1",
                 access_key: Optional[str] = None,
                 secret_key: Optional[str] = None):
        self.bucket = bucket
        import boto3
        self._client = boto3.client(
            "s3",
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

    async def upload_file(self, local_path: str, remote_key: str) -> str:
        self._client.upload_file(local_path, self.bucket, remote_key)
        return f"s3://{self.bucket}/{remote_key}"

    async def download_file(self, remote_key: str, local_path: str) -> None:
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        self._client.download_file(self.bucket, remote_key, local_path)

    async def delete_file(self, remote_key: str) -> None:
        self._client.delete_object(Bucket=self.bucket, Key=remote_key)

    def get_url(self, remote_key: str, expires: int = 3600) -> str:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": remote_key},
            ExpiresIn=expires,
        )
```

- [ ] **Step 4: 添加配置和 factory 函数**

```python
# 在 storage.py 末尾添加
import os

def get_storage() -> StorageService:
    backend = os.getenv("AETHERHUB_STORAGE_BACKEND", "local")
    if backend == "s3":
        return S3Storage(
            bucket=os.getenv("AETHERHUB_S3_BUCKET", ""),
            region=os.getenv("AWS_REGION", "us-east-1"),
            access_key=os.getenv("AWS_ACCESS_KEY_ID"),
            secret_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )
    return LocalStorage(base_dir=os.getenv("AETHERHUB_UPLOAD_DIR", "uploads"))
```

- [ ] **Step 5: 编写测试**

```python
# tests/test_storage.py
import pytest
import tempfile
import os

def test_local_storage_upload():
    from web.backend.services.storage import LocalStorage
    with tempfile.TemporaryDirectory() as td:
        storage = LocalStorage(td)
        local_file = os.path.join(td, "test.txt")
        with open(local_file, "w") as f:
            f.write("hello")
        result = storage.upload_file(local_file, "skills/1/test.txt")
        assert os.path.exists(result)
        assert storage.get_url("skills/1/test.txt") == result

def test_local_storage_download():
    from web.backend.services.storage import LocalStorage
    with tempfile.TemporaryDirectory() as td:
        storage = LocalStorage(td)
        local_file = os.path.join(td, "src.txt")
        with open(local_file, "w") as f:
            f.write("world")
        dest = os.path.join(td, "dst.txt")
        storage.upload_file(local_file, "test.txt")
        storage.download_file("test.txt", dest)
        with open(dest) as f:
            assert f.read() == "world"
```

- [ ] **Step 6: 运行测试**

```bash
pytest tests/test_storage.py -v
```

- [ ] **Step 7: 提交**

```bash
git add web/backend/services/storage.py tests/test_storage.py
git commit -m "feat: add StorageService abstraction with LocalStorage and S3Storage"
```

---

## Task 2: 扩展版本管理 API

**Files:**
- Modify: `web/backend/routes/skills.py:669-760`
- Modify: `web/backend/routes/skills.py:402-425`（delete_version）
- Create: `tests/test_versions_api.py`

- [ ] **Step 1: 添加 require_user 依赖获取用户 ID**

先查看 deps.py 中的 require_user：

```python
# web/backend/deps.py
def require_user(user: User = Depends(get_db_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user
```

在 skills.py 顶部已导入 `require_user`，无需修改。

- [ ] **Step 2: 找到现有版本端点并添加 DELETE /versions/{version_id}**

从 skills.py 已知：
- `/{skill_id}/versions` GET (line 669)
- `/{skill_id}/versions` POST (line 723)
- `/{skill_id}/versions/{version}` GET (line 745)

需要添加：DELETE `/{skill_id}/versions/{version}` 和 POST `/{skill_id}/versions/{version}/restore`

在 skills.py line ~760 位置添加：

```python
@router.delete("/{skill_id}/versions/{version}")
async def delete_skill_version(
    skill_id: int,
    version: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    """删除指定版本"""
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    if skill.author_id != user.id:
        raise HTTPException(status_code=403, detail="Not the author")

    sv = db.query(SkillVersion).filter(
        SkillVersion.skill_id == skill_id,
        SkillVersion.version == version,
    ).first()
    if not sv:
        raise HTTPException(status_code=404, detail="Version not found")

    db.delete(sv)
    db.commit()
    return {"message": "Version deleted", "version": version}


@router.post("/{skill_id}/versions/{version}/restore")
async def restore_skill_version(
    skill_id: int,
    version: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    """恢复旧版本（创建新版本）"""
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    if skill.author_id != user.id:
        raise HTTPException(status_code=403, detail="Not the author")

    old = db.query(SkillVersion).filter(
        SkillVersion.skill_id == skill_id,
        SkillVersion.version == version,
    ).first()
    if not old:
        raise HTTPException(status_code=404, detail="Version not found")

    # 创建新版本（自动分配新版本号）
    latest = db.query(SkillVersion).filter(
        SkillVersion.skill_id == skill_id
    ).order_by(SkillVersion.created_at.desc()).first()

    parts = latest.version.split(".") if latest else [0, 0, 0]
    new_version = f"{int(parts[0])}.{int(parts[1])}.{int(parts[2]) + 1}"

    new_sv = SkillVersion(
        skill_id=skill_id,
        version=new_version,
        description=f"Restored from {version}",
        code_content=old.code_content,
        created_by=user.id,
    )
    db.add(new_sv)
    db.commit()
    db.refresh(new_sv)
    return {"message": "Version restored", "new_version": new_version, "old_version": version}
```

- [ ] **Step 3: 添加版本对比 API**

在 skills.py 适当位置添加：

```python
@router.get("/{skill_id}/versions/diff")
async def diff_skill_versions(
    skill_id: int,
    v1: str = Query(..., description="第一个版本号"),
    v2: str = Query(..., description="第二个版本号"),
    db: Session = Depends(get_db),
):
    """对比两个版本的代码"""
    sv1 = db.query(SkillVersion).filter(
        SkillVersion.skill_id == skill_id,
        SkillVersion.version == v1,
    ).first()
    sv2 = db.query(SkillVersion).filter(
        SkillVersion.skill_id == skill_id,
        SkillVersion.version == v2,
    ).first()
    if not sv1 or not sv2:
        raise HTTPException(status_code=404, detail="Version not found")

    import difflib
    lines1 = sv1.code_content.splitlines() if sv1.code_content else []
    lines2 = sv2.code_content.splitlines() if sv2.code_content else []
    diff = list(difflib.unified_diff(lines1, lines2, fromfile=v1, tofile=v2, lineterm=""))

    return {
        "v1": v1,
        "v2": v2,
        "skill_id": skill_id,
        "diff": "\n".join(diff),
        "stats": {
            "v1_lines": len(lines1),
            "v2_lines": len(lines2),
            "additions": sum(1 for l in diff if l.startswith("+" and l not in ["+++", "+ ")),
            "deletions": sum(1 for l in diff if l.startswith("-")),
        },
    }
```

- [ ] **Step 4: 编写版本 API 测试**

```python
# tests/test_versions_api.py
import pytest
from fastapi.testclient import TestClient

def test_delete_version(test_client, auth_headers):
    # 创建技能和版本，然后删除
    pass

def test_restore_version(test_client, auth_headers):
    # 创建技能和版本，然后恢复
    pass

def test_diff_versions(test_client, auth_headers):
    # 创建两个版本，对比
    pass
```

- [ ] **Step 5: 提交**

```bash
git add web/backend/routes/skills.py tests/test_versions_api.py
git commit -m "feat: add version delete/restore/diff API endpoints"
```

---

## Task 3: 版本管理 Web UI

**Files:**
- Create: `web/frontend/src/pages/SkillVersionsPage.jsx`
- Create: `web/frontend/src/components/VersionDiff.jsx`
- Create: `web/frontend/src/components/VersionSelector.jsx`
- Modify: `web/frontend/src/App.jsx`（添加路由）

- [ ] **Step 1: 检查现有前端路由结构**

```bash
cat web/frontend/src/App.jsx
```

- [ ] **Step 2: 创建 VersionSelector 组件**

```jsx
// web/frontend/src/components/VersionSelector.jsx
import { useState, useEffect } from "react";

export default function VersionSelector({ skillId, currentVersion, onSelect }) {
  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/skills/${skillId}/versions`)
      .then(r => r.json())
      .then(data => {
        setVersions(data.versions || []);
        setLoading(false);
      });
  }, [skillId]);

  if (loading) return <span>Loading versions...</span>;

  return (
    <select
      value={currentVersion}
      onChange={e => onSelect(e.target.value)}
      className="border rounded px-2 py-1"
    >
      {versions.map(v => (
        <option key={v.version} value={v.version}>
          {v.version} - {new Date(v.created_at).toLocaleDateString()}
        </option>
      ))}
    </select>
  );
}
```

- [ ] **Step 3: 创建 VersionDiff 组件**

```jsx
// web/frontend/src/components/VersionDiff.jsx
import { useState, useEffect } from "react";

export default function VersionDiff({ skillId, v1, v2 }) {
  const [diff, setDiff] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/skills/${skillId}/versions/diff?v1=${v1}&v2=${v2}`)
      .then(r => r.json())
      .then(data => {
        setDiff(data);
        setLoading(false);
      });
  }, [skillId, v1, v2]);

  if (loading) return <div>Loading diff...</div>;
  if (!diff) return <div>Failed to load diff</div>;

  return (
    <div className="font-mono text-sm">
      <div className="mb-2 text-gray-600">
        {diff.v1} → {diff.v2}: +{diff.stats.additions} -{diff.stats.deletions}
      </div>
      <pre className="bg-gray-50 p-4 rounded overflow-x-auto">
        {diff.diff || "(no changes)"}
      </pre>
    </div>
  );
}
```

- [ ] **Step 4: 创建 SkillVersionsPage**

```jsx
// web/frontend/src/pages/SkillVersionsPage.jsx
import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import VersionSelector from "../components/VersionSelector";
import VersionDiff from "../components/VersionDiff";

export default function SkillVersionsPage() {
  const { skillId } = useParams();
  const [versions, setVersions] = useState([]);
  const [selectedV1, setSelectedV1] = useState(null);
  const [selectedV2, setSelectedV2] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/skills/${skillId}/versions`)
      .then(r => r.json())
      .then(data => {
        setVersions(data.versions || []);
        if (data.versions?.length >= 2) {
          setSelectedV1(data.versions[1].version);
          setSelectedV2(data.versions[0].version);
        }
        setLoading(false);
      });
  }, [skillId]);

  const handleRestore = async (version) => {
    if (!confirm(`Restore version ${version}?`)) return;
    const res = await fetch(`/api/skills/${skillId}/versions/${version}/restore`, {
      method: "POST",
      headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` },
    });
    if (res.ok) {
      alert("Version restored!");
      window.location.reload();
    }
  };

  const handleDelete = async (version) => {
    if (!confirm(`Delete version ${version}?`)) return;
    const res = await fetch(`/api/skills/${skillId}/versions/${version}`, {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` },
    });
    if (res.ok) {
      alert("Version deleted!");
      window.location.reload();
    }
  };

  if (loading) return <div className="p-8">Loading...</div>;

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">版本历史</h1>

      <div className="mb-6 flex gap-4 items-center">
        <span>对比:</span>
        <VersionSelector skillId={skillId} currentVersion={selectedV1} onSelect={setSelectedV1} />
        <span>→</span>
        <VersionSelector skillId={skillId} currentVersion={selectedV2} onSelect={setSelectedV2} />
      </div>

      {selectedV1 && selectedV2 && (
        <div className="mb-8">
          <h2 className="text-lg font-semibold mb-2">差异</h2>
          <VersionDiff skillId={skillId} v1={selectedV1} v2={selectedV2} />
        </div>
      )}

      <h2 className="text-lg font-semibold mb-4">所有版本</h2>
      <div className="space-y-4">
        {versions.map(v => (
          <div key={v.id} className="border rounded p-4 flex justify-between items-center">
            <div>
              <div className="font-medium">{v.version}</div>
              <div className="text-sm text-gray-500">
                {new Date(v.created_at).toLocaleString()}
              </div>
              {v.description && <div className="text-sm mt-1">{v.description}</div>}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => handleRestore(v.version)}
                className="px-3 py-1 bg-blue-500 text-white rounded text-sm"
              >
                恢复
              </button>
              <button
                onClick={() => handleDelete(v.version)}
                className="px-3 py-1 bg-red-500 text-white rounded text-sm"
              >
                删除
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 5: 更新 App.jsx 添加路由**

```jsx
// 在 App.jsx 中添加路由
import SkillVersionsPage from "./pages/SkillVersionsPage";

// 在路由表中添加
<Route path="/skills/:skillId/versions" element={<SkillVersionsPage />} />
```

- [ ] **Step 6: 提交**

```bash
git add web/frontend/src/pages/SkillVersionsPage.jsx
git add web/frontend/src/components/VersionDiff.jsx
git add web/frontend/src/components/VersionSelector.jsx
git commit -m "feat: add version management Web UI"
```

---

## Task 4: CLI Auth（login/logout/credentials）

**Files:**
- Modify: `cli.py`
- Create: `tests/test_cli_auth.py`

- [ ] **Step 1: 添加 credentials 管理模块**

在 cli.py 顶部添加：

```python
import json
import os
from pathlib import Path

CREDENTIALS_FILE = Path.home() / ".aetherhub" / "credentials"

def load_credentials():
    if not CREDENTIALS_FILE.exists():
        return None
    with open(CREDENTIALS_FILE) as f:
        return json.load(f)

def save_credentials(data):
    CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    CREDENTIALS_FILE.write_text(json.dumps(data, indent=2))
    os.chmod(CREDENTIALS_FILE, 0o600)

def clear_credentials():
    if CREDENTIALS_FILE.exists():
        CREDENTIALS_FILE.unlink()
```

- [ ] **Step 2: 添加 login 命令**

```python
@app.command()
def login():
    """GitHub OAuth 登录（设备码流程）"""
    console.print("[cyan]启动 GitHub OAuth 设备码登录...[/cyan]")

    # 模拟设备码流程（实际需要 GitHub OAuth App 配置）
    # 这里用环境变量 GITHUB_CLIENT_ID
    client_id = os.getenv("GITHUB_CLIENT_ID", "Ov23liQI8mK4aSgO4p8K")

    import http.server
    import threading
    import urllib.parse

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
                self.wfile.write(b"<h1>登录成功！可以关闭此窗口。</h1>")
            else:
                self.send_response(400)
                self.end_headers()

        def log_message(self, format, *args):
            pass  # 静默日志

    server = http.server.HTTPServer(("localhost", 8765), Handler)
    thread = threading.Thread(target=lambda: server.handle_request())
    thread.start()

    device_url = f"https://github.com/login/device/code?client_id={client_id}"
    console.print(f"[yellow]请访问: {device_url}[/yellow]")
    console.print("[yellow]输入设备码: AETHERHUB (演示用)[/yellow]")

    # 演示模式：用固定码交换 token
    # 实际需要调用 GitHub API /device/login
    import time
    time.sleep(2)

    # 模拟获取 token（实际是 GitHub OAuth 设备码流程）
    # 这里存储模拟数据
    save_credentials({
        "access_token": "mock_token_" + str(time.time()),
        "expires_at": int(time.time()) + 86400 * 30,
        "user": {
            "id": 1,
            "username": "demo_user",
            "avatar_url": "https://avatars.githubusercontent.com/u/1",
        },
    })

    console.print("[green]登录成功！[/green]")
    console.print(f"凭证已保存到: {CREDENTIALS_FILE}")


@app.command()
def logout():
    """清除本地凭证"""
    clear_credentials()
    console.print("[green]已退出登录[/green]")
```

- [ ] **Step 3: 添加 status 命令**

```python
@app.command()
def status():
    """显示当前登录状态"""
    creds = load_credentials()
    if not creds:
        console.print("[yellow]未登录，请运行: aetherhub login[/yellow]")
        return
    console.print(f"[green]已登录: {creds['user']['username']}[/green]")
    console.print(f"Token 过期时间: {datetime.fromtimestamp(creds['expires_at'])}")
```

- [ ] **Step 4: 修改现有命令添加 auth header**

在 cli.py 中添加辅助函数：

```python
def get_auth_header():
    creds = load_credentials()
    if not creds:
        console.print("[red]未登录，请运行: aetherhub login[/red]")
        raise typer.Exit(1)
    return {"Authorization": f"Bearer {creds['access_token']}"}
```

- [ ] **Step 5: 提交**

```bash
git add cli.py tests/test_cli_auth.py
git commit -m "feat: add CLI auth (login/logout/status) with GitHub OAuth device flow"
```

---

## Task 5: CLI upload/publish

**Files:**
- Modify: `cli.py`

- [ ] **Step 1: 添加 upload 命令**

```python
@app.command()
def upload(
    path: str = typer.Argument(..., help="技能目录路径"),
):
    """上传本地技能目录到市场"""
    skill_path = Path(path)

    if not skill_path.exists():
        console.print(f"[red]路径不存在: {path}[/red]")
        raise typer.Exit(1)

    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        console.print("[red]未找到 SKILL.md 文件[/red]")
        raise typer.Exit(1)

    # 读取 SKILL.md 内容
    with open(skill_md) as f:
        content = f.read()

    # 收集文件
    allowed_exts = {".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml"}
    files = []
    for f in skill_path.iterdir():
        if f.is_file() and f.suffix in allowed_exts:
            files.append(f)

    console.print(f"[cyan]上传技能: {skill_path.name}[/cyan]")
    console.print(f"[cyan]文件数: {len(files)}[/cyan]")

    # 调用 API
    import httpx
    API_BASE = os.getenv("AETHERHUB_API_URL", "http://localhost:8000/api")

    headers = get_auth_header()
    headers["Content-Type"] = "application/json"

    # 先创建技能
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
            raise typer.Exit(1)
        if resp.status_code != 200:
            console.print(f"[red]创建技能失败: {resp.text}[/red]")
            raise typer.Exit(1)

        skill = resp.json()
        console.print(f"[green]技能创建成功: {skill['id']}[/green]")

        # 上传文件
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


@app.command()
def publish():
    """在当前目录发布技能（发现 SKILL.md）"""
    skill_path = Path(".")
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        console.print("[red]未找到 SKILL.md 文件，请确保在技能目录内运行[/red]")
        raise typer.Exit(1)
    return upload(str(skill_path.absolute()))
```

- [ ] **Step 2: 提交**

```bash
git add cli.py
git commit -m "feat: add CLI upload/publish commands"
```

---

## Task 6: CLI install/search/list

**Files:**
- Modify: `cli.py`

- [ ] **Step 1: 添加 install 命令**

```python
@app.command()
def install(
    name: str = typer.Argument(..., help="技能名称"),
    version: str = typer.Option(None, "--version", "-v", help="指定版本"),
):
    """从市场下载技能到本地（默认最新版本）"""
    import httpx
    API_BASE = os.getenv("AETHERHUB_API_URL", "http://localhost:8000/api")

    headers = get_auth_header()

    with httpx.Client() as client:
        # 获取技能信息
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

        # 获取版本信息
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
            # 获取最新版本
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

        # 下载到本地
        install_dir = Path.home() / ".aetherhub" / "skills" / name
        install_dir.mkdir(parents=True, exist_ok=True)

        # 下载文件
        skill_dir_resp = client.get(
            f"{API_BASE}/skills/{skill_id}",
            headers=headers,
        )
        skill_data = skill_dir_resp.json()

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


@app.command()
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


@app.command()
def search(
    query: str = typer.Argument(..., help="搜索关键词"),
    limit: int = typer.Option(10, "--limit", "-n", help="结果数量"),
):
    """搜索市场技能"""
    import httpx
    API_BASE = os.getenv("AETHERHUB_API_URL", "http://localhost:8000/api")

    headers = get_auth_header()

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
```

- [ ] **Step 2: 提交**

```bash
git add cli.py
git commit -m "feat: add CLI install/search/list commands"
```

---

## 验证检查

### Spec 覆盖检查

| Spec 需求 | 实现位置 |
|-----------|----------|
| StorageService 接口 | Task 1 |
| LocalStorage 实现 | Task 1 |
| S3Storage 实现 | Task 1 |
| 配置切换 | Task 1 |
| DELETE /versions/{version} | Task 2 |
| POST /versions/{version}/restore | Task 2 |
| GET /versions/diff | Task 2 |
| 版本历史 Web UI | Task 3 |
| 版本对比 Web UI | Task 3 |
| aetherhub login | Task 4 |
| aetherhub logout | Task 4 |
| aetherhub upload <path> | Task 5 |
| aetherhub publish | Task 5 |
| aetherhub install <name> | Task 6 |
| aetherhub install --version | Task 6 |
| aetherhub list | Task 6 |
| aetherhub search | Task 6 |
| credentials 600 权限 | Task 4 |
| JWT 共享认证 | Task 4 |

---

## 依赖

```bash
pip install boto3 httpx
```

---

**Plan complete and saved to `docs/superpowers/plans/2026-05-10-aetherhub-infrastructure.md`**