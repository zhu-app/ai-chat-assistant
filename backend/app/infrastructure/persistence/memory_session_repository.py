from datetime import datetime, timezone

from app.domain import ChatMessage, ChatSession
from app.repositories.session_repository import SessionRepository


class InMemorySessionRepository(SessionRepository):
    def __init__(self) -> None:
        self.sessions: dict[str, ChatSession] = {}
        self.messages: dict[str, list[ChatMessage]] = {}
        self.share_tokens: dict[str, tuple[str, str, bool]] = {}

    def list_sessions(self, user_id: str | None = None) -> list[ChatSession]:
        sessions = self.sessions.values()
        if user_id:
            sessions = [s for s in sessions if s.user_id == user_id]
        return sorted(sessions, key=lambda item: item.updated_at, reverse=True)

    def search_sessions(self, query: str, user_id: str | None = None) -> list[ChatSession]:
        query_lower = query.lower()
        matched = []
        for session in self.sessions.values():
            if user_id and session.user_id != user_id:
                continue
            if query_lower in session.title.lower():
                matched.append(session)
                continue
            msgs = self.messages.get(session.id, [])
            for msg in msgs:
                if query_lower in (msg.content or '').lower():
                    matched.append(session)
                    break
        return sorted(matched, key=lambda item: item.updated_at, reverse=True)

    def create_session(self, session: ChatSession) -> ChatSession:
        self.sessions[session.id] = session
        self.messages.setdefault(session.id, [])
        return session

    def get_session(self, session_id: str) -> ChatSession | None:
        return self.sessions.get(session_id)

    def delete_session(self, session_id: str) -> None:
        self.sessions.pop(session_id, None)
        self.messages.pop(session_id, None)
        self.revoke_share_tokens(session_id)

    def save_message(self, message: ChatMessage) -> ChatMessage:
        items = self.messages.setdefault(message.session_id, [])
        for index, current in enumerate(items):
            if current.id == message.id:
                items[index] = message
                break
        else:
            items.append(message)
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

    def create_share_token(self, token: str, session_id: str, expires_at: str) -> None:
        self.share_tokens[token] = (session_id, expires_at, False)

    def get_shared_session_id(self, token: str, now: str) -> str | None:
        shared = self.share_tokens.get(token)
        if not shared:
            return None
        session_id, expires_at, revoked = shared
        return session_id if not revoked and expires_at > now else None

    def revoke_share_tokens(self, session_id: str) -> int:
        revoked = 0
        for token, (shared_session_id, expires_at, is_revoked) in list(self.share_tokens.items()):
            if shared_session_id == session_id and not is_revoked:
                self.share_tokens[token] = (shared_session_id, expires_at, True)
                revoked += 1
        return revoked
