# AI Chat Assistant 🤖

> 一个生产就绪的全栈 AI 聊天应用，支持多用户、知识库 RAG、流式回复。  
> 技术栈：**Vue 3 + FastAPI + LangChain + SQLite + Docker**

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
| 🔐 **用户认证**（JWT 登录/注册） | ✅ |
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
| 🔄 **CI/CD**（GitHub Actions） | ✅ |
| 🧪 **单元测试**（后端） | ✅ |

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
npm run dev -- --host 127.0.0.1 --port 5173
```

访问 `http://127.0.0.1:5173`

---

## 🐳 Docker 部署（服务器）

### 1️⃣ 准备

```bash
# 1. 克隆代码到服务器
git clone <你的仓库地址>
cd cursor_project_1

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

### 4️⃣ 管理

```bash
# 查看日志
docker compose logs -f

# 更新版本
git pull
docker compose up -d --build

# 停止
docker compose down

# 数据备份（SQLite 数据库 + 上传文档）
cp -r backend/data ./backup-$(date +%Y%m%d)
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

```env
OPENAI_API_KEY=                 # 你的 API Key（不填则走本地模拟）
OPENAI_MODEL=glm-4-flash        # 模型名
OPENAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
APP_CORS_ORIGINS=[“http://localhost:5173”, “http://127.0.0.1:5173”]
PERSISTENCE_BACKEND=sqlite
SQLITE_PATH=data/chat.db
ENABLE_RAG=true
RAG_CHUNK_SIZE=800
RAG_CHUNK_OVERLAP=120
RAG_TOP_K=4
```

### 生产环境（backend/.env.production）

```env
OPENAI_API_KEY=                 # ⚠️ 必须填入有效 Key
OPENAI_MODEL=glm-4-flash
OPENAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
APP_CORS_ORIGINS=[“http://your-domain.com”,”https://your-domain.com”]
PERSISTENCE_BACKEND=sqlite
SQLITE_PATH=/app/data/chat.db
```

---

## RAG 使用方式

1. 启动前后端
2. 右侧参数面板开启「启用 RAG」
3. 点击「上传文档」
4. 选择 `txt / md / pdf / docx`
5. 在文档列表中勾选当前会话要参与检索的文档
6. 提问与文档内容相关的问题

---

## 测试

```bash
cd backend
python -m unittest discover -s tests -p “test_*.py”
```

---

## 后续扩展方向

- [ ] 用户认证 + 多用户隔离
- [ ] 深色/浅色主题切换
- [ ] 移动端响应式适配
- [ ] 对话导出（Markdown / 图片）
- [ ] 会话 / 消息搜索
- [ ] Token 用量统计
- [ ] 异步文档索引
- [ ] 多模态支持（图片识别）