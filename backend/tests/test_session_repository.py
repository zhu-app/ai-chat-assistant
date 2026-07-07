import unittest
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
        self.repository.save_message(ChatMessage(session_id=session.id, role='user', content='hello'))

        sessions = self.repository.list_sessions()
        messages = self.repository.list_messages(session.id)

        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0].title, 'repo test')
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].content, 'hello')


if __name__ == '__main__':
    unittest.main()