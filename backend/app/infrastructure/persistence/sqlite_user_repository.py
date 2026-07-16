import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.domain import User
from app.repositories.user_repository import UserRepository


class SqliteUserRepository(UserRepository):
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
            connection.executescript('''
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    hashed_password TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
            ''')

    @staticmethod
    def _to_user(row: sqlite3.Row) -> User:
        return User(
            id=row['id'],
            username=row['username'],
            hashed_password=row['hashed_password'],
            created_at=row['created_at'],
        )

    def list_users(self) -> list[User]:
        with self._connect() as connection:
            rows = connection.execute(
                'SELECT * FROM users ORDER BY created_at DESC'
            ).fetchall()
        return [self._to_user(row) for row in rows]

    def get_by_username(self, username: str) -> User | None:
        with self._connect() as connection:
            row = connection.execute(
                'SELECT * FROM users WHERE username = ?', (username.lower().strip(),)
            ).fetchone()
        return self._to_user(row) if row else None

    def get_by_id(self, user_id: str) -> User | None:
        with self._connect() as connection:
            row = connection.execute(
                'SELECT * FROM users WHERE id = ?', (user_id,)
            ).fetchone()
        return self._to_user(row) if row else None

    def create(self, username: str, hashed_password: str) -> User:
        user = User(username=username.lower().strip(), hashed_password=hashed_password)
        with self._connect() as connection:
            connection.execute(
                'INSERT INTO users (id, username, hashed_password, created_at) VALUES (?, ?, ?, ?)',
                (user.id, user.username, user.hashed_password, user.created_at),
            )
        return user

    def cleanup_guest_users(self, days: int = 7) -> int:
        """删除指定天数前的游客用户及其关联数据。"""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        with self._connect() as connection:
            # 找出过期游客用户
            expired = connection.execute(
                "SELECT id FROM users WHERE username LIKE '游客_%' AND created_at < ?",
                (cutoff,),
            ).fetchall()
            expired_ids = [row['id'] for row in expired]
            if not expired_ids:
                return 0
            # 级联删除会话和消息
            placeholders = ','.join('?' * len(expired_ids))
            connection.execute(
                f"DELETE FROM messages WHERE session_id IN (SELECT id FROM sessions WHERE user_id IN ({placeholders}))",
                expired_ids,
            )
            connection.execute(
                f"DELETE FROM sessions WHERE user_id IN ({placeholders})",
                expired_ids,
            )
            connection.execute(
                f"DELETE FROM users WHERE id IN ({placeholders})",
                expired_ids,
            )
        return len(expired_ids)