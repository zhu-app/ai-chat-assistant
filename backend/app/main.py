import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.chat import router as chat_router
from app.api.routes.health import router as health_router
from app.core.config import settings
from app.core.rate_limiter import RateLimitMiddleware

logger = logging.getLogger(__name__)


async def _cleanup_guest_users():
    """定时清理 7 天前的游客用户，防止数据库膨胀。"""
    try:
        from app.infrastructure.persistence.sqlite_user_repository import SqliteUserRepository
        repo = SqliteUserRepository(settings.sqlite_path)
        deleted = repo.cleanup_guest_users(days=7)
        if deleted:
            logger.info('已清理 %d 个过期游客用户', deleted)
    except Exception as exc:
        logger.warning('游客清理任务失败: %s', exc)


async def _periodic_cleanup():
    """每 24 小时运行一次清理。"""
    while True:
        await asyncio.sleep(86400)  # 24 小时
        await _cleanup_guest_users()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时运行一次清理
    await _cleanup_guest_users()
    # 启动后台定时任务
    task = asyncio.create_task(_periodic_cleanup())
    yield
    # 关闭时取消任务
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.app_cors_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.add_middleware(RateLimitMiddleware)  # 速率限制（必须在路由之前添加）

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(chat_router)