import sqlite3
from pathlib import Path

from app.domain import ChatMessage, ChatSession
from app.repositories.session_repository import SessionRepository


class SqliteSessionRepository(SessionRepository):
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute('PRAGMA journal_mode=WAL')
        connection.execute('PRAGMA synchronous=NORMAL')
        return connection

    def _init_schema(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                '''
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL DEFAULT '',
                    title TEXT NOT NULL,
                    model TEXT NOT NULL,
                    system_prompt TEXT NOT NULL,
                    temperature REAL NOT NULL DEFAULT 0.7,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
                );
                '''
            )
            # 兼容旧表
            for col in ['temperature', 'user_id']:
                try:
                    connection.execute(f'ALTER TABLE sessions ADD COLUMN {col} TEXT' if col == 'user_id'
                                       else f'ALTER TABLE sessions ADD COLUMN {col} REAL NOT NULL DEFAULT 0.7')
                except Exception:
                    pass

    @staticmethod
    def _to_session(row: sqlite3.Row) -> ChatSession:
        return ChatSession(
            id=row['id'],
            user_id=str(row['user_id']) if 'user_id' in row.keys() else '',
            title=row['title'],
            model=row['model'],
            system_prompt=row['system_prompt'],
            temperature=row['temperature'] if 'temperature' in row.keys() else 0.7,
            created_at=row['created_at'],
            updated_at=row['updated_at'],
        )

    @staticmethod
    def _to_message(row: sqlite3.Row) -> ChatMessage:
        return ChatMessage(
            id=row['id'],
            session_id=row['session_id'],
            role=row['role'],
            content=row['content'],
            status=row['status'],
            created_at=row['created_at'],
        )

    def list_sessions(self, user_id: str | None = None) -> list[ChatSession]:
        with self._connect() as connection:
            if user_id:
                rows = connection.execute(
                    'SELECT * FROM sessions WHERE user_id = ? ORDER BY updated_at DESC', (user_id,)
                ).fetchall()
            else:
                rows = connection.execute('SELECT * FROM sessions ORDER BY updated_at DESC').fetchall()
        return [self._to_session(row) for row in rows]

    def search_sessions(self, query: str, user_id: str | None = None) -> list[ChatSession]:
        """按标题或消息内容搜索会话。"""
        like = f'%{query}%'
        with self._connect() as connection:
            if user_id:
                rows = connection.execute(
                    '''SELECT DISTINCT s.* FROM sessions s
                       LEFT JOIN messages m ON m.session_id = s.id
                       WHERE (s.title LIKE ? OR m.content LIKE ?) AND s.user_id = ?
                       ORDER BY s.updated_at DESC''',
                    (like, like, user_id),
                ).fetchall()
            else:
                rows = connection.execute(
                    '''SELECT DISTINCT s.* FROM sessions s
                       LEFT JOIN messages m ON m.session_id = s.id
                       WHERE s.title LIKE ? OR m.content LIKE ?
                       ORDER BY s.updated_at DESC''',
                    (like, like),
                ).fetchall()
        return [self._to_session(row) for row in rows]

    def create_session(self, session: ChatSession) -> ChatSession:
        with self._connect() as connection:
            connection.execute(
                'INSERT INTO sessions (id, user_id, title, model, system_prompt, temperature, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (session.id, session.user_id, session.title, session.model, session.system_prompt, session.temperature, session.created_at, session.updated_at),
            )
        return session

    def get_session(self, session_id: str) -> ChatSession | None:
        with self._connect() as connection:
            row = connection.execute('SELECT * FROM sessions WHERE id = ?', (session_id,)).fetchone()
        return self._to_session(row) if row else None

    def delete_session(self, session_id: str) -> None:
        with self._connect() as connection:
            connection.execute('DELETE FROM messages WHERE session_id = ?', (session_id,))
            connection.execute('DELETE FROM sessions WHERE id = ?', (session_id,))

    def save_message(self, message: ChatMessage) -> ChatMessage:
        with self._connect() as connection:
            connection.execute(
                'INSERT OR REPLACE INTO messages (id, session_id, role, content, status, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                (message.id, message.session_id, message.role, message.content, message.status, message.created_at),
            )
        self.touch_session(message.session_id)
        return message

    def list_messages(self, session_id: str) -> list[ChatMessage]:
        with self._connect() as connection:
            rows = connection.execute(
                'SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC',
                (session_id,),
            ).fetchall()
        return [self._to_message(row) for row in rows]

    def update_message_content(self, message_id: str, content: str) -> None:
        with self._connect() as connection:
            connection.execute('UPDATE messages SET content = ? WHERE id = ?', (content, message_id))

    def touch_session(self, session_id: str, title: str | None = None, temperature: float | None = None) -> ChatSession | None:
        session = self.get_session(session_id)
        if not session:
            return None
        from datetime import datetime, timezone

        updated_at = datetime.now(timezone.utc).isoformat()
        next_title = title or session.title
        next_temp = temperature if temperature is not None else session.temperature
        with self._connect() as connection:
            connection.execute(
                'UPDATE sessions SET title = ?, temperature = ?, updated_at = ? WHERE id = ?',
                (next_title, next_temp, updated_at, session_id),
            )
        return self.get_session(session_id)