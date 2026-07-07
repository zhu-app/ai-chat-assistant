import sqlite3
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