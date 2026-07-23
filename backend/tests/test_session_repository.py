import unittest
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.domain import ChatMessage, ChatSession
from app.infrastructure.persistence.sqlite_session_repository import SqliteSessionRepository


class SqliteSessionRepositoryTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.db_path = Path('tests/tmp/test-chat.db')
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        if self.db_path.exists():
            self.db_path.unlink()
        self.repository = SqliteSessionRepository(str(self.db_path))

    def tearDown(self) -> None:
        if self.db_path.exists():
            self.db_path.unlink()

    def test_create_session_and_persist_messages(self):
        session = ChatSession(title='repo test')
        self.repository.create_session(session)
        self.repository.save_message(ChatMessage(
            session_id=session.id,
            role='user',
            content='hello',
            metadata={'sources': [{'filename': 'guide.txt'}], 'telemetry': {'inputTokens': 12}},
        ))

        sessions = self.repository.list_sessions()
        messages = self.repository.list_messages(session.id)

        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0].title, 'repo test')
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].content, 'hello')
        self.assertEqual(messages[0].metadata['sources'][0]['filename'], 'guide.txt')
        self.assertEqual(messages[0].metadata['telemetry']['inputTokens'], 12)

    def test_share_tokens_expire_and_can_be_revoked(self):
        session = self.repository.create_session(ChatSession(title='shared'))
        now = datetime.now(timezone.utc)
        self.repository.create_share_token(
            'valid-token',
            session.id,
            (now + timedelta(hours=1)).isoformat(),
        )
        self.repository.create_share_token(
            'expired-token',
            session.id,
            (now - timedelta(hours=1)).isoformat(),
        )

        self.assertEqual(
            self.repository.get_shared_session_id('valid-token', now.isoformat()),
            session.id,
        )
        self.assertIsNone(
            self.repository.get_shared_session_id('expired-token', now.isoformat())
        )
        self.assertEqual(self.repository.revoke_share_tokens(session.id), 2)
        self.assertIsNone(
            self.repository.get_shared_session_id('valid-token', now.isoformat())
        )

    def test_legacy_database_is_migrated_on_startup(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / 'legacy.db'
            connection = sqlite3.connect(db_path)
            try:
                connection.executescript(
                    '''
                    CREATE TABLE sessions (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL DEFAULT '',
                        title TEXT NOT NULL,
                        model TEXT NOT NULL,
                        system_prompt TEXT NOT NULL,
                        temperature REAL NOT NULL DEFAULT 0.7,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );
                    CREATE TABLE messages (
                        id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        status TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    );
                    CREATE TABLE share_tokens (
                        token TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    );
                    '''
                )
                connection.commit()
            finally:
                connection.close()

            repository = SqliteSessionRepository(str(db_path))
            session = repository.create_session(ChatSession(title='migrated'))
            repository.save_message(ChatMessage(
                session_id=session.id,
                role='assistant',
                content='answer',
                metadata={'sources': [{'filename': 'legacy.txt'}]},
            ))

            message = repository.list_messages(session.id)[0]
            self.assertEqual(message.metadata['sources'][0]['filename'], 'legacy.txt')
            self.assertIsNone(
                repository.get_shared_session_id('legacy-token', datetime.now(timezone.utc).isoformat())
            )


if __name__ == '__main__':
    unittest.main()
