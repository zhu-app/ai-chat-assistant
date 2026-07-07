from typing import AsyncIterator, Protocol

from app.domain import ChatMessage, SessionSettings


class ChatProvider(Protocol):
    async def stream_reply(
        self,
        history: list[ChatMessage],
        settings: SessionSettings,
        context_docs: list[str] | None = None,
    ) -> AsyncIterator[str]: ...