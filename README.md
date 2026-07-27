# 知聊 AI Chat Assistant

品牌名称为「知聊」—— 一个面向个人和小团队的全栈 AI 聊天助手。

提供 Vue 3 前端、FastAPI 后端、SQLite 持久化、SSE 流式输出、知识库 RAG、多 Agent 协作、对话分享、响应遥测和 Docker 一键部署能力。

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)
![Vue](https://img.shields.io/badge/Vue-3.5-4FC08D?logo=vue.js)
![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178C6?logo=typescript)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)

---

## 功能亮点

### 💬 智能对话
- 多用户注册 / 登录 / 游客模式，JWT 鉴权与登录态过期隔离
- 多会话管理，支持流式回复、停止生成、消息编辑
- 会话搜索、重命名、导出（Markdown / 图片）
- 欢迎引导页 + 快速场景模板（写作、编程、翻译、总结、头脑风暴、学习）

### 📚 知识库 RAG
- 支持上传 `txt`、`md`、`pdf`、`docx` 文档
- 后台异步索引，问答时自动检索并展示来源
- 文档列表管理，支持重试索引和删除

### 🤖 Multi-Agent 协作
- 自动规划执行步骤，展示 Agent 计划与执行过程
- 质量审查机制，提升回复准确性

### 📊 响应遥测
- 首字延迟、总耗时、Token 估算、成本估算
- 质量评分面板，便于追踪和优化

### 🔗 对话分享
- 只读分享链接，支持 Markdown 渲染
- 可设置过期时间和手动撤销

### 🛡️ 安全与工程
- Markdown 渲染经 DOMPurify 安全过滤
- 接口限流、CSP 安全头、生产配置校验
- 游客数据自动清理
- Docker Compose 一键部署（Nginx + 后端健康检查）

---

## 技术栈

| 模块 | 技术 |
|------|------|
| 前端 | Vue 3, TypeScript, Vite, Vitest |
| 后端 | FastAPI, Pydantic, LangChain, python-jose, passlib |
| LLM | OpenAI 兼容 Chat Completions 接口 |
| 存储 | SQLite, 本地文档存储 |
| 部署 | Docker, Docker Compose, Nginx |

---

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

---

## 快速开始

### 本地开发

#### 1. 后端

```bash
cd backend
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env   # macOS / Linux
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

如果想先跑通界面而不调用真实模型，开启 Mock 模式：

```env
LLM_MOCK=true
```

#### 2. 前端

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 **http://127.0.0.1:5173**

前端默认请求 `/api`。开发环境由 Vite 代理转发到后端；如需直连，可配置：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

### Docker 部署

准备生产环境变量：

```bash
cp backend/.env.production.example backend/.env.production
```

编辑 `backend/.env.production`，至少设置 `OPENAI_API_KEY`、`JWT_SECRET_KEY`、`APP_CORS_ORIGINS`。

启动：

```bash
docker compose up -d --build
```

默认将前端暴露在宿主机 `80` 端口，后端只在 Compose 网络内暴露 `8000`，由前端 Nginx 转发 `/api`。

---

## 常用命令

```bash
# 后端测试
cd backend && python -m unittest discover -s tests -v

# 前端测试
cd frontend && npm test -- --cache=false

# 前端构建
cd frontend && npm run build

# Docker 配置检查
docker compose config --quiet
```

---

## API 概览

主要接口都挂在 `/api` 下：

### 认证
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 注册 |
| POST | `/api/auth/login` | 登录 |
| POST | `/api/auth/guest` | 游客登录 |
| GET | `/api/auth/me` | 当前用户信息 |

### 会话
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/sessions` | 会话列表 |
| GET | `/api/sessions/search` | 搜索会话 |
| POST | `/api/sessions` | 创建会话 |
| PATCH | `/api/sessions/{session_id}` | 更新标题或设置 |
| GET | `/api/sessions/{session_id}/messages` | 会话消息 |
| PATCH | `/api/sessions/{session_id}/messages/{message_id}` | 编辑用户消息 |

### 聊天
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/chat/stream` | SSE 流式聊天 |

### 文档
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/documents` | 文档列表 |
| POST | `/api/documents` | 上传文档 |
| POST | `/api/documents/{document_id}/retry` | 重试索引 |
| DELETE | `/api/documents/{document_id}` | 删除文档 |

### 分享
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/sessions/{session_id}/share` | 创建分享链接 |
| GET | `/api/sessions/shared/{share_token}` | 读取分享内容 |
| DELETE | `/api/sessions/{session_id}/share` | 撤销分享 |

### 健康检查
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health/live` | 存活检查 |
| GET | `/api/health/ready` | 就绪检查 |

---

## 环境变量

详细配置见 `backend/.env.example` 和 `backend/.env.production.example`。

| 变量 | 说明 |
|------|------|
| `OPENAI_API_KEY` | OpenAI 兼容接口密钥 |
| `OPENAI_BASE_URL` | OpenAI 兼容接口地址 |
| `OPENAI_MODEL` | 默认模型 |
| `LLM_MOCK` | 设为 `true` 时强制使用 Mock 模型 |
| `JWT_SECRET_KEY` | JWT 签名密钥，生产环境必须替换 |
| `APP_CORS_ORIGINS` | 允许跨域访问的前端源 |
| `CHAT_CONTEXT_MAX_TOKENS` | 聊天上下文最大估算 Token |
| `CHAT_CONTEXT_RECENT_MESSAGES` | 强制保留的最近消息数 |
| `SHARE_LINK_TTL_HOURS` | 分享链接有效期，默认 168 小时 |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | 普通 API 限流，默认 `60` |
| `AUTH_RATE_LIMIT_REQUESTS_PER_MINUTE` | 登录/注册/游客限流，默认 `10` |

---

## 安全与数据

- 不要提交真实的 `.env`、`.env.production`、数据库或上传文档，仓库已通过 `.gitignore` 忽略
- 生产环境必须更换 `JWT_SECRET_KEY`，并将 `APP_CORS_ORIGINS` 限制为真实域名
- 前端 Markdown 输出经过 DOMPurify 过滤，Nginx 配置了 CSP、安全响应头和静态资源缓存
- 游客账号在启动和运行期间定期清理，包含会话、消息、分享链接、文档、索引和本地文件
- SQLite 数据和上传文档默认位于 `backend/data/`，Docker 部署时通过卷挂载持久化

---

## 测试状态

| 模块 | 测试数 | 状态 |
|------|--------|------|
| 后端单元测试 | 20 项 | ✅ 全部通过 |
| 前端单元测试 | 2 项 | ✅ 全部通过 |
| 前端构建 | — | ✅ `npm run build` 通过 |
| Docker 配置 | — | ✅ `docker compose config --quiet` 通过 |

---

## 近期代码审查（2026-07-27）

已完成全量代码审查，覆盖后端 4400 行、前端 3900 行代码。修复以下问题：

| # | 类型 | 问题 | 修复 |
|:-:|:----:|:-----|:----:|
| 1 | 🐛 Bug | 空 `sessionId` 发送消息后流结束清空所有消息 | `runSend` 新增 `newSessionCreated` 标志位 |
| 2 | 🐛 Bug | 分享页面不渲染 Markdown | 引入 `marked` + `DOMPurify` 渲染 |
| 3 | 🎨 UI | 空会话标题"新对话"在侧栏和顶部重复显示 | 空会话时显示"准备开始新的对话" |
| 4 | 🐛 Bug | 消息编辑后 `updated_at` 不更新 | 编辑时同步更新时间戳 |
| 5 | ⚡ 性能 | `MessageList` 中 highlight.js 异步加载竞态 | 加载完成前降级为纯文本 |
| 6 | 🛡 安全 | `revoke_share_tokens` 返回 `rowcount` 可能为 -1 | 改用 `SELECT changes()` |

---

## License

MIT
