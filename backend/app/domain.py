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