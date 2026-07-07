import asyncio
from typing import AsyncIterator

from app.core.config import settings as app_settings
from app.domain import ChatMessage, RetrievedChunk, SessionSettings
from app.llm.providers.base import ChatProvider
from app.repositories.retrieval_repository import RetrievalRepository
from app.repositories.session_repository import SessionRepository
from app.services.session_service import SessionService

# 单次 token 流超时（秒），防止 LLM 挂死
_TOKEN_TIMEOUT = 120.0


class ChatService:
    def __init__(
        self,
        session_service: SessionService,
        session_repository: SessionRepository,
        provider: ChatProvider,
        retriever: RetrievalRepository,
    ) -> None:
        self.session_service = session_service
        self.session_repository = session_repository
        self.provider = provider
        self.retriever = retriever

    @staticmethod
    async def _timeout_stream(stream: AsyncIterator[str]) -> AsyncIterator[str]:
        """为每个 token 添加超时保护，防止 LLM 挂死"""
        try:
            while True:
                token = await asyncio.wait_for(stream.__anext__(), timeout=_TOKEN_TIMEOUT)
                yield token
        except asyncio.TimeoutError:
            raise TimeoutError('LLM 响应超时，请重试') from None
        except StopAsyncIteration:
            return

    @staticmethod
    def _format_context_docs(chunks: list[RetrievedChunk]) -> list[str]:
        return [f'[{chunk.filename}]\n{chunk.content}' for chunk in chunks]

    @staticmethod
    def _format_sources(chunks: list[RetrievedChunk]) -> list[dict]:
        return [
            {
                'documentId': chunk.document_id,
                'filename': chunk.filename,
                'score': chunk.score,
                'chunkIndex': chunk.chunk_index,
                'preview': chunk.content[:180],
            }
            for chunk in chunks
        ]

    async def stream_chat(
        self,
        session_id: str | None,
        user_message: str,
        settings: SessionSettings,
        user_id: str = '',
    ) -> AsyncIterator[dict]:
        session = self.session_service.get_or_create_session(session_id, settings, user_id=user_id)

        # 全局 RAG 开关：后端可强制禁用 RAG
        if not app_settings.enable_rag:
            settings.use_rag = False

        title = user_message[:24] or '新对话'
        self.session_repository.touch_session(
            session.id,
            title=title if session.title == '新对话' else None,
            temperature=settings.temperature,
        )

        user_entry = ChatMessage(session_id=session.id, role='user', content=user_message, status='done')
        self.session_repository.save_message(user_entry)

        assistant_entry = ChatMessage(session_id=session.id, role='assistant', content='', status='streaming')

        yield {
            'type': 'session_created',
            'sessionId': session.id,
            'meta': {
                'title': self.session_repository.get_session(session.id).title,
                'temperature': session.temperature,
            },
        }
        yield {
            'type': 'message_started',
            'sessionId': session.id,
            'messageId': assistant_entry.id,
        }

        history = self.session_repository.list_messages(session.id)
        retrieved_chunks = self.retriever.retrieve(user_message, settings.document_ids) if settings.use_rag else []
        context_docs = self._format_context_docs(retrieved_chunks)

        try:
            async for token in self._timeout_stream(
                self.provider.stream_reply(history, settings, context_docs)
            ):
                assistant_entry.content += token
                yield {
                    'type': 'token',
                    'sessionId': session.id,
                    'messageId': assistant_entry.id,
                    'delta': token,
                }
        except asyncio.CancelledError:
            # 客户端断开 SSE 连接，保存已生成的部分并标记为 aborted
            assistant_entry.status = 'aborted'
            self.session_repository.save_message(assistant_entry)
            return
        except GeneratorExit:
            # 生成器被关闭（aclose），同样视为中断
            assistant_entry.status = 'aborted'
            self.session_repository.save_message(assistant_entry)
            return
        except Exception as exc:
            assistant_entry.status = 'error'
            self.session_repository.save_message(assistant_entry)
            yield {
                'type': 'error',
                'sessionId': session.id,
                'messageId': assistant_entry.id,
                'meta': {'message': str(exc)},
            }
            return

        assistant_entry.status = 'done'
        self.session_repository.save_message(assistant_entry)
        yield {
            'type': 'message_done',
            'sessionId': session.id,
            'messageId': assistant_entry.id,
            'meta': {
                'content': assistant_entry.content,
                'sources': self._format_sources(retrieved_chunks),
            },
        }