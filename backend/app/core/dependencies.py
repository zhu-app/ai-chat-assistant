from functools import lru_cache

from fastapi import Header, HTTPException

from app.core.auth import decode_access_token
from app.core.config import settings
from app.infrastructure.persistence.memory_session_repository import InMemorySessionRepository
from app.infrastructure.persistence.sqlite_document_repository import SqliteDocumentRepository
from app.infrastructure.persistence.sqlite_session_repository import SqliteSessionRepository
from app.infrastructure.persistence.sqlite_user_repository import SqliteUserRepository
from app.infrastructure.retrieval.embedding_engine import EmbeddingEngine
from app.infrastructure.retrieval.hybrid_retriever import HybridRetriever
from app.llm.providers.openai_chat import OpenAICompatibleChatProvider
from app.repositories.document_repository import DocumentRepository
from app.repositories.retrieval_repository import RetrievalRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import UserRepository
from app.services.chat_service import ChatService
from app.services.document_service import DocumentService
from app.services.session_service import SessionService


@lru_cache
def get_session_repository() -> SessionRepository:
    if settings.persistence_backend == 'memory':
        return InMemorySessionRepository()
    return SqliteSessionRepository(settings.sqlite_path)


@lru_cache
def get_document_repository() -> DocumentRepository:
    return SqliteDocumentRepository(settings.sqlite_path)


@lru_cache
def get_embedding_engine() -> EmbeddingEngine:
    return EmbeddingEngine()


@lru_cache
def get_retriever() -> RetrievalRepository:
    return HybridRetriever(get_document_repository(), get_embedding_engine(), settings.rag_top_k)


@lru_cache
def get_provider() -> OpenAICompatibleChatProvider:
    return OpenAICompatibleChatProvider()


@lru_cache
def get_session_service() -> SessionService:
    return SessionService(get_session_repository())


@lru_cache
def get_document_service() -> DocumentService:
    return DocumentService(
        repository=get_document_repository(),
        embedding_engine=get_embedding_engine(),
        store_dir=settings.document_store_dir,
        chunk_size=settings.rag_chunk_size,
        chunk_overlap=settings.rag_chunk_overlap,
    )


@lru_cache
def get_user_repository() -> UserRepository:
    return SqliteUserRepository(settings.sqlite_path)


def get_current_user(authorization: str = Header('')) -> str:
    """
    从 Authorization header 提取 Bearer token 并返回用户 ID。
    可直接用于 FastAPI 依赖注入。
    """
    if not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='未登录或 token 无效')
    token = authorization.removeprefix('Bearer ')
    payload = decode_access_token(token)
    if payload is None or 'sub' not in payload:
        raise HTTPException(status_code=401, detail='token 已过期或无效')
    return str(payload['sub'])


def get_chat_service() -> ChatService:
    from app.agents.agent_pipeline import AgentPipeline
    from app.core.telemetry import ResponseEvaluator
    from app.llm.prompt_optimizer import PromptOptimizer

    provider = get_provider()
    retriever = get_retriever()

    # 仅在启用时创建 PromptOptimizer（节省内存）
    prompt_optimizer = None
    if settings.enable_prompt_optimizer:
        prompt_optimizer = PromptOptimizer(provider)

    # 始终创建 AgentPipeline（内部已延迟初始化，不阻塞）
    # 用户可在会话中随时开启/关闭 Agent 模式
    agent_pipeline = AgentPipeline(provider, retriever)

    # 质量评估器（始终可用）
    response_evaluator = ResponseEvaluator(provider)

    return ChatService(
        session_service=get_session_service(),
        session_repository=get_session_repository(),
        provider=provider,
        retriever=retriever,
        prompt_optimizer=prompt_optimizer,
        agent_pipeline=agent_pipeline,
        response_evaluator=response_evaluator,
    )