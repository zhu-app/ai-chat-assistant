from abc import ABC, abstractmethod

from app.domain import ChatMessage, ChatSession


class SessionRepository(ABC):
    @abstractmethod
    def list_sessions(self, user_id: str | None = None) -> list[ChatSession]: ...

    @abstractmethod
    def search_sessions(self, query: str, user_id: str | None = None) -> list[ChatSession]: ...

    @abstractmethod
    def create_session(self, session: ChatSession) -> ChatSession: ...

    @abstractmethod
    def get_session(self, session_id: str) -> ChatSession | None: ...

    @abstractmethod
    def delete_session(self, session_id: str) -> None: ...

    @abstractmethod
    def save_message(self, message: ChatMessage) -> ChatMessage: ...

    @abstractmethod
    def list_messages(self, session_id: str) -> list[ChatMessage]: ...

    @abstractmethod
    def touch_session(self, session_id: str, title: str | None = None, temperature: float | None = None) -> ChatSession | None: ...

    @abstractmethod
    def create_share_token(self, token: str, session_id: str, expires_at: str) -> None: ...

    @abstractmethod
    def get_shared_session_id(self, token: str, now: str) -> str | None: ...

    @abstractmethod
    def revoke_share_tokens(self, session_id: str) -> int: ...
