from typing import AsyncIterator, Protocol, runtime_checkable

from app.domain import ChatMessage, SessionSettings


class ChatProvider(Protocol):
    async def stream_reply(
        self,
        history: list[ChatMessage],
        settings: SessionSettings,
        context_docs: list[str] | None = None,
    ) -> AsyncIterator[str]: ...

    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        model: str = '',
    ) -> str: ...

    async def stream_complete(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        model: str = '',
    ) -> AsyncIterator[str]: ...