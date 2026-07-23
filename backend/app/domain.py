from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

MessageRole = Literal['user', 'assistant', 'system']
MessageStatus = Literal['pending', 'streaming', 'done', 'error', 'aborted']
DocumentStatus = Literal['uploaded', 'processing', 'ready', 'error']


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class User:
    id: str = field(default_factory=lambda: str(uuid4()))
    username: str = ''
    hashed_password: str = ''
    created_at: str = field(default_factory=utc_now)


@dataclass
class SessionSettings:
    model: str = 'glm-4-flash'
    temperature: float = 0.7
    system_prompt: str = '你是一个清晰、直接、可靠的中文 AI 助手。'
    use_rag: bool = False
    document_ids: list[str] = field(default_factory=list)
    # — Prompt 优化引擎 —
    enable_prompt_optimizer: bool = False
    # — Multi-Agent 协作模式 —
    enable_agent_mode: bool = False
    # — 联网搜索 —
    enable_web_search: bool = False


@dataclass
class AgentStep:
    """一个 Agent 执行步骤的记录"""
    agent_name: str
    agent_label: str
    task: str
    result: str = ''
    status: str = 'pending'  # pending | running | done | error


@dataclass
class ChatSession:
    id: str = field(default_factory=lambda: str(uuid4()))
    user_id: str = ''
    title: str = '新对话'
    model: str = 'glm-4-flash'
    system_prompt: str = '你是一个清晰、直接、可靠的中文 AI 助手。'
    temperature: float = 0.7
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)


@dataclass
class ChatMessage:
    session_id: str
    role: MessageRole
    content: str
    status: MessageStatus = 'done'
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=utc_now)
    metadata: dict = field(default_factory=dict)


@dataclass
class KnowledgeDocument:
    filename: str
    content_type: str
    storage_path: str
    user_id: str = ''
    status: DocumentStatus = 'uploaded'
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=utc_now)


@dataclass
class DocumentChunk:
    document_id: str
    chunk_index: int
    content: str
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=utc_now)


@dataclass
class DocumentChunkVector:
    chunk_id: str
    document_id: str
    chunk_index: int
    vector: list[float]
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=utc_now)


@dataclass
class RetrievedChunk:
    document_id: str
    filename: str
    content: str
    score: int
    chunk_index: int = 0


@dataclass
class ResponseTelemetry:
    """响应的遥测数据（性能、成本、质量）"""
    # 性能
    first_token_latency_ms: float = 0.0
    total_duration_ms: float = 0.0
    tokens_per_second: float = 0.0
    # Token
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    # RAG（如有）
    rag_chunks_retrieved: int = 0
    rag_top_score: float = 0.0
    # 质量自评（如有）
    quality_score: float = 0.0
    quality_details: dict = field(default_factory=dict)
