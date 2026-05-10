# AetherHub 企业化基础设施设计

**日期**: 2026-05-10
**版本**: v1.0
**范围**: 存储抽象层 + 版本管理 UI + CLI 用户端工作流

---

## 1. 背景与目标

当前 AetherHub 的短板：
- **存储**: 硬编码本地 `uploads/`，无 S3 支持
- **版本管理**: DB 有但 Web UI 缺失
- **CLI**: 只有 `run`/`verify`/`execute`，面向开发者，缺用户端工作流

目标：Phase 3 企业化基础设施，支撑：
- 生产级文件存储（S3 + 本地 fallback）
- 完整版本管理（读/切/比/删/发布）
- 终端用户 CLI（login/upload/publish/install/search/list）

---

## 2. 架构概览

```
用户
  ├── Web UI（版本历史/版本对比/版本切换）
  └── CLI（login / upload / publish / install / search / list / logout）
                      │
              ┌───────┴───────┐
              ▼               ▼
        Auth Service     Storage Service
        (共享JWT)         ┌─────────┐
              │          │ LocalFS │ ← fallback（开发模式）
              │          └─────────┘
              │          ┌─────────┐
              └──────────│   S3    │ ← production
                         └─────────┘

认证: Web 和 CLI 共享 JWT，通过 GitHub OAuth 获取
存储: StorageService 接口，LocalStorage/S3Storage 双实现，配置切换
```

---

## 3. Storage 抽象层

### 3.1 接口定义

```python
# web/backend/services/storage.py
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
```

### 3.2 实现

| 实现 | 类名 | 说明 |
|------|------|------|
| 本地 | `LocalStorage` | `uploads/` 目录，硬编码 fallback |
| S3 | `S3Storage` | boto3，预签名 URL，TTL 可配置 |

### 3.3 配置

```python
# web/backend/config.py
STORAGE_BACKEND = os.getenv("AETHERHUB_STORAGE_BACKEND", "local")  # "local" | "s3"
S3_BUCKET = os.getenv("AETHERHUB_S3_BUCKET", "")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
```

### 3.4 迁移策略

现有 `SkillFile.file_path` 继续指向本地路径，S3 上传后路径格式为 `skills/{skill_id}/{filename}`。

---

## 4. 版本管理

### 4.1 数据模型（已存在）

```python
# skill_versions 表
id, skill_id, version, filesnapshot(JSON), created_at, created_by
```

### 4.2 新增 API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/{skill_id}/versions` | GET | 列出所有版本（分页） |
| `/{skill_id}/versions` | POST | 创建新版本（快照当前文件） |
| `/{skill_id}/versions/{version}` | GET | 获取特定版本详情 |
| `/{skill_id}/versions/{version}` | DELETE | 删除版本 |
| `/{skill_id}/versions/{version}/restore` | POST | 恢复旧版本（创建新版本） |
| `/{skill_id}/versions/diff` | GET | 对比两个版本（?v1=1.0&v2=1.1） |

### 4.3 Web UI 功能

- **版本历史页**: 列表展示所有版本，时间/作者/备注
- **版本详情**: 查看该版本的所有文件内容
- **版本切换**: 一键切换到旧版本（restore）
- **版本对比**: side-by-side diff，使用 `difflib` 或 monaco-editor
- **版本创建**: 上传新版本时自动快照

### 4.4 版本号规则

遵循语义化版本 `MAJOR.MINOR.PATCH`（如 `1.2.0`），同一 skill 下版本号唯一。

---

## 5. CLI 用户端工作流

### 5.1 命令列表

| 命令 | 说明 |
|------|------|
| `aetherhub login` | GitHub OAuth 登录（打开浏览器） |
| `aetherhub logout` | 清除本地凭证 |
| `aetherhub upload <path>` | 上传本地技能目录到市场 |
| `aetherhub publish` | 在技能目录内运行，发现 SKILL.md 上传 |
| `aetherhub install <name>` | 从市场下载技能到本地（默认最新版本） |
| `aetherhub install <name> --version 1.2.0` | 指定版本 |
| `aetherhub list` | 列出已安装到本地的技能 |
| `aetherhub search <query>` | 搜索市场技能 |

### 5.2 认证流程

```
aetherhub login
  → 打开浏览器 GitHub OAuth 设备码流程
  → 用户在终端输入设备码授权
  → 回调获取 JWT access_token
  → 存到 ~/.aetherhub/credentials（600权限）

后续命令自动读取 credentials，附加到请求头:
Authorization: Bearer <token>
```

凭证文件格式（JSON）:
```json
{
  "access_token": "eyJ...",
  "expires_at": 1700000000,
  "user": { "id": 1, "username": "xxx", "avatar_url": "..." }
}
```

### 5.3 upload / publish 行为

**`aetherhub upload <path>`**:
- 读取 `<path>/SKILL.md` 作为 metadata
- 扫描 `<path>/*` 所有允许的文件类型（`.py`, `.md`, `.txt`, `.json`, `.yaml`, `.yml`, `.toml`）
- 通过 StorageService 上传到市场
- 触发 Z3 验证（异步）

**`aetherhub publish`**:
- 在当前目录查找 `SKILL.md`
- 未找到则报错退出
- 等价于 `upload .`

### 5.4 install 行为

**`aetherhub install <name>`**:
- 调用 API 获取技能最新版本信息
- 通过 StorageService 下载所有文件到 `~/.aetherhub/skills/<name>/`
- 下载完成后在本地注册

**`aetherhub install <name> --version 1.2.0`**:
- 同上，但指定版本号

### 5.5 本地技能目录结构

```
~/.aetherhub/
  credentials          # JWT 凭证
  skills/              # 已安装技能
    my-skill/
      SKILL.md
      skill.py
      README.md
```

---

## 6. 错误处理

| 场景 | 处理 |
|------|------|
| S3 上传失败 | 回退到 LocalStorage，记录警告日志 |
| JWT 过期 | 提示 `aetherhub login` 重新认证 |
| 版本号冲突 | API 返回 409，提示用户指定新版本号 |
| 技能下载失败 | 重试 3 次，报告错误 |

---

## 7. 安全考虑

- 凭证文件权限 `600`，不共享
- S3 预签名 URL TTL 默认 1 小时
- 上传文件类型白名单校验（后端已有）
- CLI 和 Web 共用同一套 JWT 验证中间件

---

## 8. 实现顺序

1. **Storage 抽象层**（LocalStorage + S3Storage）
2. **CLI auth**（login/logout/credentials）
3. **版本管理 API**（补全所有端点）
4. **版本管理 Web UI**（历史/对比/切换）
5. **CLI upload/publish**
6. **CLI install/search/list**

---