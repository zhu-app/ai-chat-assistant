# Docker 部署

## 目录职责

```text
frontend/Dockerfile         # 构建前端静态资源并交给 nginx 对外服务
backend/Dockerfile          # 运行 FastAPI API
deploy/nginx.conf           # 前端静态资源与 /api 反向代理
backend/.env.production.example
docker-compose.yml
```

## 启动前准备

1. 复制生产环境变量

```bash
cp backend/.env.production.example backend/.env.production
```

2. 填写真实模型密钥与域名白名单

重点字段：
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `APP_CORS_ORIGINS`
- `MAX_UPLOAD_BYTES`
- `ALLOWED_DOCUMENT_EXTENSIONS`

3. 确保服务器开放 80 端口

## 启动

```bash
docker compose up -d --build
```

## 持久化

当前使用宿主机目录挂载：

```text
./backend/data:/app/data
```

其中包括：
- `chat.db`
- `documents/`

因此容器重建后，会话和上传文档不会丢失。

## 健康检查

浏览器访问：

- `http://your-server/`
- `http://your-server/health`
- `http://your-server/health/live`
- `http://your-server/health/ready`

接口语义：

```text
/live   -> 进程是否存活
/ready  -> SQLite 路径、文档目录、模型配置、上传限制是否已装配
```

## 备份建议

第一版先按宿主机目录做定时备份：

```text
备份源:
- ./backend/data/chat.db
- ./backend/data/documents/

建议策略:
- 每日一次全量压缩
- 保留最近 7 天
- 备份文件写到独立目录或对象存储
```

## 当前部署形态

```text
浏览器
-> nginx(frontend 容器)
-> /api 反代到 backend 容器
-> SQLite + 文档文件卷
```

## 下一步建议

当前是单机正式版骨架，后续可继续补：
- HTTPS
- 自动备份脚本
- 日志采集
- 向量索引独立存储
- PostgreSQL 替换 SQLite