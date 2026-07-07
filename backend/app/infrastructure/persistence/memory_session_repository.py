from datetime import datetime, timezone

from app.domain import ChatMessage, ChatSession
from app.repositories.session_repository import SessionRepository


class InMemorySessionRepository(SessionRepository):
    def __init__(self) -> None:
        self.sessions: dict[str, ChatSession] = {}
        self.messages: dict[str, list[ChatMessage]] = {}

    def list_sessions(self, user_id: str | None = None) -> list[ChatSession]:
        sessions = self.sessions.values()
        if user_id:
            sessions = [s for s in sessions if s.user_id == user_id]
        return sorted(sessions, key=lambda item: item.updated_at, reverse=True)

    def create_session(self, session: ChatSession) -> ChatSession:
        self.sessions[session.id] = session
        self.messages.setdefault(session.id, [])
        return session

    def get_session(self, session_id: str) -> ChatSession | None:
        return self.sessions.get(session_id)

    def delete_session(self, session_id: str) -> None:
        self.sessions.pop(session_id, None)
        self.messages.pop(session_id, None)

    def save_message(self, message: ChatMessage) -> ChatMessage:
        self.messages.setdefault(message.session_id, []).append(message)
        self.touch_session(message.session_id)
        return message

    def list_messages(self, session_id: str) -> list[ChatMessage]:
        return self.messages.get(session_id, [])

    def touch_session(self, session_id: str, title: str | None = None, temperature: float | None = None) -> ChatSession | None:
        session = self.sessions.get(session_id)
        if not session:
            return None
        session.updated_at = datetime.now(timezone.utc).isoformat()
        if title:
            session.title = title
        if temperature is not None:
            session.temperature = temperature
        return session