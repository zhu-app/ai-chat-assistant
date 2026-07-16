from app.core.errors import SessionForbiddenError, SessionNotFoundError
from app.domain import ChatMessage, ChatSession, SessionSettings
from app.repositories.session_repository import SessionRepository


class SessionService:
    def __init__(self, repository: SessionRepository) -> None:
        self.repository = repository

    @staticmethod
    def _is_owner(session: ChatSession, user_id: str) -> bool:
        """
        判断当前用户是否有权访问会话。

        兼容历史数据：user_id 为空的旧会话视为无主，仅允许在明确传入 user_id
        时由调用方决定是否接管；默认拒绝跨用户访问。
        """
        if not user_id:
            return False
        # 旧数据无归属时，不允许被任意用户读写（安全优先）
        if not session.user_id:
            return False
        return session.user_id == user_id

    def require_session_owner(self, session_id: str, user_id: str) -> ChatSession:
        """获取会话并校验归属，失败抛出 SessionNotFound/Forbidden。"""
        if not session_id:
            raise SessionNotFoundError()
        session = self.repository.get_session(session_id)
        if not session:
            raise SessionNotFoundError()
        if not self._is_owner(session, user_id):
            # 不暴露“存在但无权”细节给枚举攻击：对外统一 404 更安全，
            # 但对已登录用户返回 403 便于前端区分。这里采用 403。
            raise SessionForbiddenError()
        return session

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

    def get_or_create_session(
        self,
        session_id: str | None,
        settings: SessionSettings,
        user_id: str = '',
    ) -> ChatSession:
        if session_id:
            session = self.repository.get_session(session_id)
            if session:
                if not self._is_owner(session, user_id):
                    raise SessionForbiddenError()
                return session
            # 客户端携带了不存在的 session_id：不静默接管他人 ID，直接新建
        return self.create_session(settings, user_id=user_id)

    def rename_session(self, session_id: str, title: str, user_id: str = '') -> ChatSession | None:
        cleaned_title = title.strip()
        if not cleaned_title:
            return None
        self.require_session_owner(session_id, user_id)
        return self.repository.touch_session(session_id, title=cleaned_title)

    def delete_session(self, session_id: str, user_id: str = '') -> None:
        self.require_session_owner(session_id, user_id)
        self.repository.delete_session(session_id)

    def list_messages(self, session_id: str, user_id: str = '') -> list[ChatMessage]:
        self.require_session_owner(session_id, user_id)
        return self.repository.list_messages(session_id)
