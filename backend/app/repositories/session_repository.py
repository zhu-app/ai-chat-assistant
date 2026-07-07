from abc import ABC, abstractmethod

from app.domain import ChatMessage, ChatSession


class SessionRepository(ABC):
    @abstractmethod
    def list_sessions(self, user_id: str | None = None) -> list[ChatSession]: ...

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