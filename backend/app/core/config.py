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
    app_environment: str = 'development'
    jwt_secret_key: str = 'change-me-in-production-use-a-random-string'
    app_admin_usernames: list[str] = Field(default_factory=list)
    app_allow_registration: bool = True
    min_password_length: int = 8
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
    chat_context_max_tokens: int = 6000
    chat_context_recent_messages: int = 16
    chat_summary_max_tokens: int = 800
    share_link_ttl_hours: int = 168

    # Prompt 优化引擎
    enable_prompt_optimizer: bool = True

    # Multi-Agent 协作
    enable_agent_mode: bool = False

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / '.env'),
        env_file_encoding='utf-8',
    )


settings = Settings()

DEFAULT_JWT_SECRETS = {
    'change-me-in-production-use-a-random-string',
    'change-me-to-a-random-string',
}


def validate_runtime_settings() -> None:
    if settings.app_environment.lower() != 'production':
        return
    if settings.jwt_secret_key in DEFAULT_JWT_SECRETS or len(settings.jwt_secret_key) < 32:
        raise RuntimeError('JWT_SECRET_KEY must be a random string of at least 32 characters in production')
    if not settings.openai_api_key:
        raise RuntimeError('OPENAI_API_KEY is required in production')
    if settings.min_password_length < 8:
        raise RuntimeError('MIN_PASSWORD_LENGTH must be at least 8 in production')
