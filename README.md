# 知聊 AI 🤖

[![在线体验](https://img.shields.io/badge/在线体验-139.199.230.22-blue?style=for-the-badge)](http://139.199.230.22/)
[![Vue 3](https://img.shields.io/badge/Vue_3-4FC08D?style=for-the-badge&logo=vue.js)](https://vuejs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker)](https://docker.com)

> 一个生产就绪的全栈 AI 聊天应用，支持多用户、知识库 RAG、流式回复。  
> 🚀 **核心亮点：Prompt 优化引擎 + Multi-Agent 协作系统 + 知识库 RAG + 对话分享**  
> 技术栈：**Vue 3 + FastAPI + LangChain + SQLite + Docker**  
> 🔗 **在线体验**: [http://139.199.230.22/](http://139.199.230.22/)

## 🏗️ 架构

```
┌─────────────────────────────────────────────────────────┐
│                    用户浏览器                            │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Vue 3 SPA                                      │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │   │
│  │  │ 登录/注册  │  │  聊天页面 │  │  设置面板     │  │   │
│  │  └──────────┘  └──────────┘  └──────────────┘  │   │
│  └─────────────────────────────────────────────────┘   │
└───────────────────────┬─────────────────────────────────┘
                        │ SSE / REST API (JWT Auth)
                        ▼
┌─────────────────────────────────────────────────────────┐
│  Nginx (反向代理 / 静态文件)                              │
└───────────────────────┬─────────────────────────────────┘
                        │
┌─────────────────────────────────────────────────────────┐
│  FastAPI Backend (Docker)                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │ Auth API  │  │ Chat API  │  │ Document / RAG API  │  │
│  │ JWT 登录   │  │ SSE 流式  │  │ 上传/检索           │  │
│  └──────────┘  └──────────┘  └──────────────────────┘  │
│                        │                                │
│  ┌──────────────────────────────────────────────────┐   │
│  │  LangChain + LLM Provider (智谱 GLM-4-Flash)      │   │
│  └──────────────────────────────────────────────────┘   │
│                        │                                │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ SQLite   │  │ 文档存储      │  │ 向量索引          │  │
│  │ 会话/消息  │  │ data/documents│  │ chunk_vectors    │  │
│  └──────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## ✨ 功能特性

| 功能 | 状态 |
|------|------|
| 🔐 **用户认证**（JWT 登录/注册/游客） | ✅ |
| 💬 **多会话管理 + 多轮聊天** | ✅ |
| ⚡ **SSE 流式回复 + 生成中断** | ✅ |
| 📚 **RAG 知识库检索**（向量 + 关键词混合） | ✅ |
| 📄 **文档上传**（txt / md / pdf / docx） | ✅ |
| 🎨 **Markdown 富文本渲染**（代码高亮 + 表格 + 引用） | ✅ |
| 🌗 **深色/浅色主题切换** | ✅ |
| 📱 **移动端响应式**（抽屉式侧栏） | ✅ |
| ⚙️ **设置持久化**（model / temperature / system prompt 跟随会话） | ✅ |
| ⏱️ **LLM 超时保护** | ✅ |
| 🐳 **Docker 容器化部署** | ✅ |
| 🧪 **单元测试**（后端） | ✅ |
| ✨ **Prompt 优化引擎** — 自动将模糊提问改写为结构化问题，提升回答质量 | ✅ |
| 🤖 **Multi-Agent 协作系统** — 编排器 + 多 Agent 并行协作 + 质量审查 | ✅ |
| 🌐 **联网搜索** — DuckDuckGo 实时搜索，普通模式和 Agent 模式均可用 | ✅ |
| 📊 **响应遥测** — 首字延迟、Token 统计、成本估算、质量自评 | ✅ |
| 🔒 **速率限制** — 滑动窗口限流，防止 abuse | ✅ |
| 🧹 **自动游客清理** — 7 天过期游客自动清理，防止数据库膨胀 | ✅ |
| 📝 **消息编辑** — 用户消息可二次编辑，修正提问 | ✅ |
| 🔗 **对话分享** — 生成分享链接，一键复制给他人 | ✅ |
| 🔍 **会话搜索** — 按标题或消息内容实时搜索（300ms 防抖） | ✅ |
| ⌨️ **键盘快捷键** — Enter 发送 / Shift+Enter 换行 / Ctrl+↑ 编辑上条 | ✅ |
| 🕐 **消息时间戳** — 相对时间显示（刚刚 / N 分钟前） | ✅ |
| 🏠 **欢迎引导页** — 6 个场景模板一键开始对话 | ✅ |
| 🎭 **系统提示词预设** — 自定义角色预设，本地持久化保存 | ✅ |
| ✏️ **对话重命名** — 双击侧栏会话名称即可修改 | ✅ |
| 📦 **对话导出** — Markdown 导出 / 图片导出（html2canvas） | ✅ |
| 📋 **文档管理对话框** — 独立弹窗管理上传文档 | ✅ |
| 🤖 **Agent 签名徽章** — 每条 AI 回复标注 Agent 协作详情 | ✅ |
| 🎛️ **折叠式设置面板** — 分类折叠，节省屏幕空间（1024px 友好） | ✅ |

## 🚀 核心新特性

### ✨ Prompt 优化引擎

传统 AI 聊天中，用户输入模糊问题时回答质量往往不佳。Prompt 优化引擎利用 LLM 自身能力，在发送前自动改写用户输入：

| 原始提问 | 优化后 |
|---------|--------|
| "讲一下 AI" | "请从定义、发展历程、核心技术、应用场景 4 个方面介绍 AI，每个方面约 200 字" |
| "Python 怎么样" | "请以资深架构师的角度分析 Python 语言的优势、劣势、适用场景以及与其他语言的对比" |

**技术实现：** 零样本（zero-shot）改写 + 结构化注入 + 角色匹配，无需训练数据

### 🤖 Multi-Agent 协作系统

不再是一个 AI 单打独斗，而是多个专业 Agent 协作完成任务：

```
用户提问 → 编排器（分析任务类型）
          ├─ 📚 知识检索 Agent → 搜索相关文档
          ├─ 🔍 深度分析 Agent → 多维度拆解（背景/方案/利弊/建议）
          ├─ 💻 代码专家 Agent → 代码编写与解释
          └─ ✍️ 内容合成 Agent → 整合所有输出 → 流式最终回答
               └─ ⭐ 质量审查 Agent → 评分 + 改进建议（可选）
```

**效果：** 复杂问题回答质量显著提升，所有 Agent 工作流在前端实时可见。

## 快速启动（开发环境）

### 后端

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
# 复制环境变量并填入 API Key
cp .env.example .env
# 编辑 backend/.env，填入 OPENAI_API_KEY
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

访问 `http://127.0.0.1:5173`

---

## 🐳 Docker 部署（服务器）

### 1️⃣ 准备

```bash
# 1. 克隆代码到服务器
git clone <你的仓库地址>
cd ai-chat-assistant

# 2. 配置生产环境变量
cp backend/.env.production.example backend/.env.production
# 编辑 backend/.env.production，填入:
#   - OPENAI_API_KEY=你的API密钥
#   - APP_CORS_ORIGINS=[“http://你的域名”]
```

### 2️⃣ 启动

```bash
docker compose up -d --build
```

### 3️⃣ 访问

浏览器打开 `http://服务器IP` 即可使用。

### 4️⃣ 更新版本

```bash
cd /root/ai-chat-assistant
git fetch origin
git reset --hard origin/master
docker compose up -d --build
```

### 生产环境注意事项

| 项目 | 建议 |
|------|------|
| 🔐 **HTTPS** | 使用 Nginx/Caddy 反向代理 + Let's Encrypt |
| 🔄 **自动重启** | docker-compose 已配置 `restart: unless-stopped` |
| 💾 **数据持久化** | SQLite 和上传文档在 `backend/data/` 卷中 |
| 🔑 **API Key** | 生产环境使用智谱 `GLM-4-Flash`（免费），如需更强模型可换 `GLM-4-Plus` |
| 🌐 **域名 + HTTPS** | 推荐 Caddy 自动申请 SSL 证书：`your.domain.com { reverse_proxy localhost:80 }` |

---

## 用户管理

### 查看所有注册用户

```bash
sqlite3 backend/data/chat.db "SELECT id, username, created_at FROM users;"
```

示例输出：
```
b7f1a2c3-...|admin|2026-07-07T12:00:00
e8d4f5g6-...|zhangsan|2026-07-07T14:30:00
```

### 删除某个用户

```bash
sqlite3 backend/data/chat.db "DELETE FROM users WHERE username='zhangsan';"
```

> ⚠️ 删除用户不会自动删除其会话和消息，如需清理：
> ```bash
> sqlite3 backend/data/chat.db "DELETE FROM messages WHERE session_id IN (SELECT id FROM sessions WHERE user_id='要删除的用户ID');"
> sqlite3 backend/data/chat.db "DELETE FROM sessions WHERE user_id='要删除的用户ID';"
> ```

### 查看某个用户的会话数量

```bash
sqlite3 backend/data/chat.db "SELECT u.username, COUNT(s.id) as sessions FROM users u LEFT JOIN sessions s ON s.user_id=u.id GROUP BY u.id;"
```

---

## 环境变量

### 开发环境（backend/.env）

详见 `backend/.env.example`：

```env
# ===== 必填 =====
OPENAI_API_KEY=                           # 你的 API Key
OPENAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4/

# ===== 模型 =====
OPENAI_MODEL=glm-4-flash

# ===== JWT 安全 =====
JWT_SECRET_KEY=change-me-to-a-random-string   # ⚠️ 生产环境务必修改

# ===== CORS =====
APP_CORS_ORIGINS=["http://localhost:5173", "http://127.0.0.1:5173"]

# ===== 持久化 =====
PERSISTENCE_BACKEND=sqlite
SQLITE_PATH=data/chat.db

# ===== RAG 知识库 =====
ENABLE_RAG=true
RAG_CHUNK_SIZE=800
RAG_CHUNK_OVERLAP=120
RAG_TOP_K=4
RAG_EMBEDDING_MODEL=embedding-3
RAG_EMBEDDING_DIMENSIONS=128

# ===== 文档上传 =====
MAX_UPLOAD_BYTES=20971520
ALLOWED_DOCUMENT_EXTENSIONS=[".txt",".md",".pdf",".docx"]
```

### 生产环境（backend/.env.production）

详见 `backend/.env.production.example`，注意路径使用 Docker 容器内绝对路径：

```env
# ===== 必填 =====
OPENAI_API_KEY=                           # ⚠️ 必须填入有效 Key
OPENAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4/

# ===== 模型 =====
OPENAI_MODEL=glm-4-flash

# ===== JWT 安全 =====
JWT_SECRET_KEY=change-me-to-a-random-string   # ⚠️ 务必修改为随机字符串

# ===== CORS =====
APP_CORS_ORIGINS=["http://your-domain.com","https://your-domain.com"]

# ===== 持久化 =====
PERSISTENCE_BACKEND=sqlite
SQLITE_PATH=/app/data/chat.db

# ===== RAG 知识库 =====
ENABLE_RAG=true
RAG_SOURCE_DIR=/app/knowledge
DOCUMENT_STORE_DIR=/app/data/documents
RAG_CHUNK_SIZE=800
RAG_CHUNK_OVERLAP=120
RAG_TOP_K=4
RAG_EMBEDDING_MODEL=embedding-3
RAG_EMBEDDING_DIMENSIONS=128

# ===== 文档上传 =====
MAX_UPLOAD_BYTES=20971520
ALLOWED_DOCUMENT_EXTENSIONS=[".txt",".md",".pdf",".docx"]
```

---

## RAG 使用方式

1. 启动前后端
2. 点击右上角 ⚙ 打开设置面板
3. 在「增强功能」中开启「RAG 知识库」
4. 在「知识库文档」中点击「管理文档」，上传文件（txt / md / pdf / docx）
5. 在文档列表中勾选当前会话要参与检索的文档
6. 提问与文档内容相关的问题

---

## 测试

```bash
cd backend
python -m unittest discover -s tests -p "test_*.py"
```

---

## 后续扩展方向

- [x] **对话导出** — Markdown 导出（✅ 已实现）、图片导出（✅ 已实现，html2canvas）
- [x] **会话 / 消息搜索** — 后端 API + 前端搜索框（✅ 已实现，300ms 防抖实时搜索）
- [x] **Token 用量统计** — 前端跨消息累积汇总（✅ 已实现，展示总Token/总成本/平均质量）
- [x] **消息编辑** — 用户消息可二次编辑（✅ 已实现）
- [x] **对话分享** — 生成分享链接（✅ 已实现）
- [x] **键盘快捷键** — Enter 发送 / Shift+Enter 换行 / Ctrl+↑ 编辑上条（✅ 已实现）
- [x] **消息时间戳** — 相对时间显示（✅ 已实现）
- [x] **欢迎引导页** — 场景模板快速开始（✅ 已实现）
- [x] **系统提示词预设** — 本地保存自定义角色（✅ 已实现）
- [x] **对话重命名** — 双击侧栏会话名称修改（✅ 已实现）
- [ ] **异步文档索引** — 上传文档后后台异步处理，不阻塞用户
- [ ] **会话归档** — 自动归档历史会话，保持侧栏整洁
- [ ] **管理员后台** — 用户管理、Token 用量统计、系统监控面板
- [ ] **i18n 国际化** — 英文界面支持


