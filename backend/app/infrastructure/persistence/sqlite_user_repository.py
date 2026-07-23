import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.core.config import settings
from app.domain import User
from app.repositories.user_repository import UserRepository


class SqliteUserRepository(UserRepository):
    def __init__(self, db_path: str, document_store_dir: str | None = None) -> None:
        self.db_path = db_path
        self.document_store_dir = document_store_dir or settings.document_store_dir
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute('PRAGMA foreign_keys=ON')
        connection.execute('PRAGMA busy_timeout=5000')
        connection.execute('PRAGMA journal_mode=WAL')
        connection.execute('PRAGMA synchronous=NORMAL')
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

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
        document_paths: list[str] = []
        with self._connect() as connection:
            # 找出过期游客用户
            expired = connection.execute(
                "SELECT id FROM users WHERE username GLOB '游客_*' AND created_at < ?",
                (cutoff,),
            ).fetchall()
            expired_ids = [row['id'] for row in expired]
            if not expired_ids:
                return 0
            placeholders = ','.join('?' * len(expired_ids))

            tables = {
                row['name']
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }
            if 'documents' in tables:
                document_paths = [
                    str(row['storage_path'])
                    for row in connection.execute(
                        f'SELECT storage_path FROM documents WHERE user_id IN ({placeholders})',
                        expired_ids,
                    ).fetchall()
                ]
            if 'share_tokens' in tables and 'sessions' in tables:
                connection.execute(
                    f'DELETE FROM share_tokens WHERE session_id IN '
                    f'(SELECT id FROM sessions WHERE user_id IN ({placeholders}))',
                    expired_ids,
                )
            if 'messages' in tables and 'sessions' in tables:
                connection.execute(
                    f'DELETE FROM messages WHERE session_id IN '
                    f'(SELECT id FROM sessions WHERE user_id IN ({placeholders}))',
                    expired_ids,
                )
            if 'sessions' in tables:
                connection.execute(
                    f'DELETE FROM sessions WHERE user_id IN ({placeholders})',
                    expired_ids,
                )
            if 'document_chunk_vectors' in tables and 'documents' in tables:
                connection.execute(
                    f'DELETE FROM document_chunk_vectors WHERE document_id IN '
                    f'(SELECT id FROM documents WHERE user_id IN ({placeholders}))',
                    expired_ids,
                )
            if 'document_chunks' in tables and 'documents' in tables:
                connection.execute(
                    f'DELETE FROM document_chunks WHERE document_id IN '
                    f'(SELECT id FROM documents WHERE user_id IN ({placeholders}))',
                    expired_ids,
                )
            if 'documents' in tables:
                connection.execute(
                    f'DELETE FROM documents WHERE user_id IN ({placeholders})',
                    expired_ids,
                )
            connection.execute(
                f"DELETE FROM users WHERE id IN ({placeholders})",
                expired_ids,
            )

        store_root = Path(self.document_store_dir).resolve()
        for raw_path in document_paths:
            path = Path(raw_path).resolve()
            try:
                path.relative_to(store_root)
            except ValueError:
                continue
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
        return len(expired_ids)
