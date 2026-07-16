from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_CORS_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
]
DEFAULT_ALLOWED_DOCUMENT_EXTENSIONS = ['.txt', '.md', '.pdf', '.docx']


def resolve_backend_path(value: str) -> str:
    path = Path(value)
    if path.is_absolute():
        return str(path)
    return str((BASE_DIR / path).resolve())


class Settings(BaseSettings):
    app_name: str = 'AI Chat Assistant'
    jwt_secret_key: str = 'change-me-in-production-use-a-random-string'
    app_cors_origins: list[str] = Field(default_factory=lambda: DEFAULT_CORS_ORIGINS.copy())
    app_log_level: str = 'INFO'
    openai_api_key: str = ''
    openai_model: str = 'glm-4-flash'
    openai_base_url: str = 'https://open.bigmodel.cn/api/paas/v4/'
    persistence_backend: str = 'sqlite'
    sqlite_path: str = resolve_backend_path('data/chat.db')
    enable_rag: bool = False
    rag_source_dir: str = resolve_backend_path('knowledge')
    document_store_dir: str = resolve_backend_path('data/documents')
    max_upload_bytes: int = 20 * 1024 * 1024
    allowed_document_extensions: list[str] = Field(default_factory=lambda: DEFAULT_ALLOWED_DOCUMENT_EXTENSIONS.copy())
    rag_chunk_size: int = 800
    rag_chunk_overlap: int = 120
    rag_top_k: int = 4
    rag_embedding_model: str = 'embedding-3'
    rag_embedding_dimensions: int = 128

    # Prompt 优化引擎
    enable_prompt_optimizer: bool = True

    # Multi-Agent 协作
    enable_agent_mode: bool = False

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / '.env'),
        env_file_encoding='utf-8',
    )


settings = Settings()

# 启动时校验关键配置
if settings.openai_api_key:
    _masked_key = settings.openai_api_key[:8] + '...' + settings.openai_api_key[-4:] if len(settings.openai_api_key) > 12 else '***'
    print(f'[配置] OpenAI API Key: {_masked_key}')
    print(f'[配置] 模型: {settings.openai_model}')
else:
    print('[警告] ⚠️  未配置 OPENAI_API_KEY！所有 AI 回复将使用本地模拟回复，不会调用真实 LLM。')
    print('[警告]    请创建 backend/.env 文件并填入 OPENAI_API_KEY')

if settings.jwt_secret_key == 'change-me-in-production-use-a-random-string':
    print('[警告] ⚠️  JWT_SECRET_KEY 使用默认值！生产环境务必修改为随机字符串。')