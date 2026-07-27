# 知聊 AI Chat Assistant

一个面向个人和小团队的全栈 AI 聊天助手，品牌名称为「知聊」。项目提供 Vue 3 前端、FastAPI 后端、SQLite 持久化、SSE 流式输出、知识库 RAG、多 Agent 协作、对话分享、响应遥测和 Docker 部署能力。

## 功能亮点

- 多用户登录、注册和游客模式，支持 JWT 鉴权与登录态过期隔离。
- 多会话聊天，支持流式回复、停止生成、消息编辑、会话搜索、重命名和导出（Markdown / 图片）。
- 文档知识库 RAG，支持上传 `txt`、`md`、`pdf`、`docx`，后台异步索引并在回答中展示来源。
- Prompt 优化与 Multi-Agent 协作，可展示 Agent 计划、执行步骤和质量审查结果。
- 响应遥测面板，展示首字延迟、总耗时、Token 估算、成本估算和质量评分。
- 只读对话分享链接（支持 Markdown 渲染），支持过期时间和撤销。
- 欢迎引导页 + 快速场景模板（写作、编程、翻译、总结、头脑风暴、学习）。
- Markdown 渲染安全过滤、生产配置校验、接口限流、CSP 安全头和游客数据自动清理。
- Docker Compose 一键部署，内置前端 Nginx 与后端健康检查。

## 技术栈

| 模块 | 技术 |
| --- | --- |
| 前端 | Vue 3, TypeScript, Vite, Vitest |
| 后端 | FastAPI, Pydantic, LangChain, python-jose, passlib |
| LLM | OpenAI 兼容 Chat Completions 接口 |
| 存储 | SQLite, 本地文档存储 |
| 部署 | Docker, Docker Compose, Nginx |

## 目录结构

```text
ai-chat-assistant/
├── backend/                # FastAPI 后端
│   ├── app/
│   │   ├── agents/         # Multi-Agent 编排与执行
│   │   ├── api/            # REST/SSE 路由和 DTO
│   │   ├── core/           # 配置、鉴权、限流
│   │   ├── infrastructure/ # SQLite 持久化实现
│   │   ├── llm/            # LLM Provider 和 Prompt 处理
│   │   └── services/       # 聊天、文档、上下文窗口服务
│   └── tests/              # 后端单元测试
├── frontend/               # Vue 3 前端
│   └── src/
│       ├── components/     # 聊天、设置、登录等组件
│       ├── composables/    # 状态与业务逻辑
│       ├── pages/          # 聊天页、登录页、分享页
│       └── services/       # API Client
├── deploy/                 # Nginx 配置
├── .github/workflows/      # CI
└── docker-compose.yml
```

## 本地开发

### 1. 后端

```bash
cd backend
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

在 `backend/.env` 中至少配置：

```env
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
JWT_SECRET_KEY=change-me-to-a-long-random-secret
APP_CORS_ORIGINS=["http://127.0.0.1:5173","http://localhost:5173"]
```

如果想先跑通界面而不调用真实模型，可以开启 Mock：

```env
LLM_MOCK=true
```

### 2. 前端

```bash
cd frontend
npm install
npm run dev
```

浏览器打开：

```text
http://127.0.0.1:5173
```

前端默认请求 `/api`。开发环境通常由 Vite 代理或本地反向代理转发到后端；如果需要直连后端，可在前端环境变量中配置：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

## Docker 部署

准备生产环境变量：

```bash
cp backend/.env.production.example backend/.env.production
```

编辑 `backend/.env.production`，至少设置：

```env
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
JWT_SECRET_KEY=replace-with-a-long-random-secret
APP_CORS_ORIGINS=["https://your-domain.com"]
```

启动：

```bash
docker compose up -d --build
```

默认会将前端暴露在宿主机 `80` 端口，后端只在 Compose 网络内暴露 `8000`，由前端 Nginx 转发 `/api`。

## 常用命令

后端测试：

```bash
cd backend
python -m unittest discover -s tests -v
```

前端测试：

```bash
cd frontend
npm test -- --cache=false
```

前端构建：

```bash
cd frontend
npm run build
```

Docker 配置检查：

```bash
docker compose config --quiet
```

## API 概览

主要接口都挂在 `/api` 下：

| 路径 | 说明 |
| --- | --- |
| `POST /api/auth/register` | 注册 |
| `POST /api/auth/login` | 登录 |
| `POST /api/auth/guest` | 游客登录 |
| `GET /api/auth/me` | 当前用户 |
| `GET /api/sessions` | 会话列表 |
| `GET /api/sessions/search` | 搜索会话 |
| `POST /api/sessions` | 创建会话 |
| `PATCH /api/sessions/{session_id}` | 更新会话标题或设置 |
| `GET /api/sessions/{session_id}/messages` | 会话消息 |
| `PATCH /api/sessions/{session_id}/messages/{message_id}` | 编辑用户消息 |
| `POST /api/chat/stream` | SSE 流式聊天 |
| `GET /api/documents` | 文档列表 |
| `POST /api/documents` | 上传文档 |
| `POST /api/documents/{document_id}/retry` | 重试文档索引 |
| `DELETE /api/documents/{document_id}` | 删除文档 |
| `POST /api/sessions/{session_id}/share` | 创建分享链接 |
| `GET /api/sessions/shared/{share_token}` | 读取分享会话 |
| `DELETE /api/sessions/{session_id}/share` | 撤销分享链接 |
| `GET /api/health/live` | 存活检查 |
| `GET /api/health/ready` | 就绪检查 |

## 环境变量

详细配置见：

- `backend/.env.example`
- `backend/.env.production.example`

常用配置：

| 变量 | 说明 |
| --- | --- |
| `OPENAI_API_KEY` | OpenAI 兼容接口密钥 |
| `OPENAI_BASE_URL` | OpenAI 兼容接口地址 |
| `OPENAI_MODEL` | 默认模型 |
| `LLM_MOCK` | 设为 `true` 时强制使用 Mock 模型，不调用真实模型（即使已配置 API Key） |
| `JWT_SECRET_KEY` | JWT 签名密钥，生产环境必须替换 |
| `APP_CORS_ORIGINS` | 允许跨域访问的前端源 |
| `CHAT_CONTEXT_MAX_TOKENS` | 聊天上下文最大估算 Token |
| `CHAT_CONTEXT_RECENT_MESSAGES` | 强制保留的最近消息数 |
| `SHARE_LINK_TTL_HOURS` | 分享链接有效期，默认 168 小时 |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | 普通 API 接口的每分钟限流阈值，默认 `60` |
| `AUTH_RATE_LIMIT_REQUESTS_PER_MINUTE` | 登录/注册/游客接口的每分钟限流阈值，默认 `10` |

## 安全与数据

- 不要提交真实的 `.env`、`.env.production`、数据库或上传文档，仓库已通过 `.gitignore` 忽略这些文件。
- 生产环境必须更换 `JWT_SECRET_KEY`，并将 `APP_CORS_ORIGINS` 限制为真实域名。
- 前端 Markdown 输出经过 DOMPurify 过滤，部署 Nginx 也配置了 CSP、安全响应头和静态资源缓存。
- 游客账号会在后端启动和运行期间定期清理，清理范围包含会话、消息、分享链接、文档、索引和本地文件。
- SQLite 数据和上传文档默认位于 `backend/data/`，Docker 部署时通过卷挂载持久化。

## 当前状态

### 代码审查（2026-07-27）

已完成全量代码审查，覆盖后端 4400 行、前端 3900 行代码。发现并修复以下问题：

| # | 类型 | 问题描述 | 修复 |
|:---:|:---:|:---|:---:|
| 1 | 🐛 Bug | 空 `sessionId` 发送消息后，流结束会清空所有消息 | ✅ 已修复 — `runSend` 新增 `newSessionCreated` 标志位 |
| 2 | 🐛 Bug | 分享页面（`/share/:token`）不渲染 Markdown，代码块显示纯文本 | ✅ 已修复 — 引入 `marked` + `DOMPurify` 渲染 |
| 3 | 🎨 UI | 空会话标题"新对话"在侧栏和顶部标题区重复显示 | ✅ 已修复 — 空会话标题区显示"准备开始新的对话" |
| 4 | 🐛 Bug | 消息编辑后会话 `updated_at` 不更新，排序不刷新 | ✅ 已修复 — 编辑时同步更新时间戳 |
| 5 | ⚡ 性能 | `MessageList` 中 highlight.js 异步加载存在竞态条件 | ✅ 已修复 — 加载完成前降级为纯文本 |
| 6 | 🛡 安全 | `revoke_share_tokens` 返回 `cursor.rowcount` 可能为 -1 | ✅ 已修复 — 改用 `SELECT changes()` |

### 测试状态

当前测试覆盖：

- **后端**：20 项单元测试（认证、会话、聊天、文档索引、分享生命周期、上下文窗口、安全配置、游客清理和限流）— **全部通过**
- **前端**：2 项单元测试（SSE 解析）— **全部通过**
- **构建检查**：`npm run build` 通过（注意：主 chunk 约 940kB，建议后续做动态拆分）
- **Docker**：`docker compose config --quiet` 通过
