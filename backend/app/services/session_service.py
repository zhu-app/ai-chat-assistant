from app.domain import ChatMessage, ChatSession, SessionSettings
from app.repositories.session_repository import SessionRepository


class SessionService:
    def __init__(self, repository: SessionRepository) -> None:
        self.repository = repository

    def list_sessions(self, user_id: str | None = None) -> list[ChatSession]:
        return self.repository.list_sessions(user_id=user_id)

    def search_sessions(self, query: str, user_id: str | None = None) -> list[ChatSession]:
        if not query.strip():
            return self.repository.list_sessions(user_id=user_id)
        return self.repository.search_sessions(query.strip(), user_id=user_id)

    def create_session(self, settings: SessionSettings | None = None, user_id: str = '') -> ChatSession:
        session = ChatSession(
            user_id=user_id,
            model=(settings.model if settings else 'glm-4-flash'),
            system_prompt=(settings.system_prompt if settings else '你是一个清晰、直接、可靠的中文 AI 助手。'),
            temperature=settings.temperature if settings else 0.7,
        )
        return self.repository.create_session(session)

    def get_or_create_session(self, session_id: str | None, settings: SessionSettings, user_id: str = '') -> ChatSession:
        session = self.repository.get_session(session_id) if session_id else None
        if session:
            return session
        return self.create_session(settings, user_id=user_id)

    def rename_session(self, session_id: str, title: str) -> ChatSession | None:
        cleaned_title = title.strip()
        if not cleaned_title:
            return None
        return self.repository.touch_session(session_id, title=cleaned_title)

    def delete_session(self, session_id: str) -> None:
        self.repository.delete_session(session_id)

    def list_messages(self, session_id: str) -> list[ChatMessage]:
        return self.repository.list_messages(session_id)
