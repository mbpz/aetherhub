# AetherHub Web 应用

AetherHub 是一个大模型技能（Skill）管理 Web 平台，提供技能广场、上传、详情、个人管理等功能。

## 技术栈

- **后端**：Python FastAPI + SQLAlchemy + SQLite
- **前端**：React 18 + Vite + TailwindCSS + Zustand
- **认证**：GitHub OAuth 2.0 + JWT

## 项目结构

```
web/
├── backend/          # FastAPI 后端
│   ├── main.py       # 应用入口
│   ├── models.py     # 数据模型
│   ├── auth.py       # GitHub OAuth + JWT
│   ├── deps.py       # FastAPI 依赖注入
│   ├── database.py   # 数据库初始化
│   ├── seed.py       # 示例数据
│   ├── routes/
│   │   ├── auth.py   # 认证路由
│   │   └── skills.py # Skill CRUD 路由
│   ├── uploads/      # 上传文件存储
│   └── data/         # SQLite 数据库文件
└── frontend/         # React 前端
    ├── src/
    │   ├── pages/    # 页面组件
    │   ├── components/ # 通用组件
    │   ├── api/      # API 封装
    │   ├── store/    # Zustand 状态管理
    │   └── lib/      # 工具函数
    └── dist/         # 构建产物
```

## 快速启动

### 1. 配置 GitHub OAuth App

1. 访问 [GitHub OAuth Apps](https://github.com/settings/developers)
2. 点击 "New OAuth App"
3. 填写信息：
   - **Application name**：AetherHub
   - **Homepage URL**：`http://localhost:5173`
   - **Authorization callback URL**：`http://localhost:8000/api/v1/auth/callback`
4. 创建后获取 `Client ID` 和 `Client Secret`

### 2. 配置环境变量

在项目根目录创建 `.env` 文件（或直接设置环境变量）：

```env
GITHUB_CLIENT_ID=你的_Client_ID
GITHUB_CLIENT_SECRET=你的_Client_Secret
GITHUB_CALLBACK_URL=http://localhost:8000/api/v1/auth/callback
JWT_SECRET_KEY=your-secure-random-secret
JWT_EXPIRE_HOURS=24
DATABASE_URL=sqlite:///./web/backend/data/aetherhub.db
AUTO_SEED=true
```

> **注意**：如果不设置 `GITHUB_CLIENT_ID` 和 `GITHUB_CLIENT_SECRET`，应用将自动进入 **Mock 模式**，点击"GitHub 登录"会直接创建一个 Demo 用户，方便本地测试。

### 3. 启动后端

```bash
# 在项目根目录
cd /path/to/aetherhub

# 创建并激活虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\activate  # Windows

# 安装依赖
pip install fastapi uvicorn sqlalchemy pyjwt httpx python-multipart

# 启动后端（自动初始化数据库和 seed 数据）
uvicorn web.backend.main:app --port 8000 --reload
```

后端启动后访问：
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

### 4. 启动前端

```bash
cd web/frontend
npm install
npm run dev
```

前端启动后访问：http://localhost:5173

## 功能说明

| 功能 | 路由 | 登录要求 |
|------|------|---------|
| 技能广场 | `/skills` | 否 |
| 技能详情 | `/skills/:id` | 否 |
| 上传技能 | `/skills/upload` | 是 |
| 我的技能 | `/mine` | 是 |
| GitHub 登录 | 导航栏按钮 | - |

## API 接口

后端 API 前缀为 `/api/v1/`，完整文档见 http://localhost:8000/docs

主要接口：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/auth/login` | 获取 GitHub OAuth URL |
| GET | `/api/v1/auth/callback` | OAuth 回调处理 |
| GET | `/api/v1/auth/me` | 获取当前用户 |
| GET | `/api/v1/skills` | 技能列表（支持搜索/过滤/分页） |
| GET | `/api/v1/skills/mine` | 我的技能（需登录） |
| GET | `/api/v1/skills/{id}` | 技能详情 |
| POST | `/api/v1/skills` | 上传技能（需登录） |
| DELETE | `/api/v1/skills/{id}` | 删除技能（需登录，仅作者） |
| POST | `/api/v1/skills/{id}/star` | Star 技能 |
| DELETE | `/api/v1/skills/{id}/star` | 取消 Star |

## Mock 模式

当未配置 GitHub OAuth 环境变量时，系统自动进入 Mock 模式：

- 点击"GitHub 登录"按钮，系统直接创建一个名为 `demo-user` 的测试账号并登录
- 无需任何 GitHub OAuth 配置即可测试所有功能

## Seed 数据

首次启动后端时，自动写入 5 个示例技能：
1. **csv-data-processor** - 数据处理
2. **http-request-tool** - 网络工具
3. **pdf-text-extractor** - 文件操作
4. **ai-text-summarizer** - AI工具
5. **file-organizer** - 系统工具
