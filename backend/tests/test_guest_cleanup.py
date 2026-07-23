import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.domain import (
    ChatMessage,
    ChatSession,
    DocumentChunk,
    DocumentChunkVector,
    KnowledgeDocument,
)
from app.infrastructure.persistence.sqlite_document_repository import SqliteDocumentRepository
from app.infrastructure.persistence.sqlite_session_repository import SqliteSessionRepository
from app.infrastructure.persistence.sqlite_user_repository import SqliteUserRepository


class GuestCleanupTestCase(unittest.TestCase):
    def test_cleanup_removes_all_guest_data_and_stored_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = str(root / 'chat.db')
            store_dir = root / 'documents'
            store_dir.mkdir()
            user_repository = SqliteUserRepository(db_path, document_store_dir=str(store_dir))
            session_repository = SqliteSessionRepository(db_path)
            document_repository = SqliteDocumentRepository(db_path)

            guest = user_repository.create('游客_expired', '')
            regular = user_repository.create('regular-user', 'hash')
            expired_at = (datetime.now(timezone.utc) - timedelta(days=8)).isoformat()
            connection = sqlite3.connect(db_path)
            try:
                connection.execute(
                    'UPDATE users SET created_at = ? WHERE id = ?',
                    (expired_at, guest.id),
                )
                connection.commit()
            finally:
                connection.close()

            session = session_repository.create_session(
                ChatSession(user_id=guest.id, title='guest session')
            )
            session_repository.save_message(
                ChatMessage(session_id=session.id, role='user', content='private')
            )
            session_repository.create_share_token(
                'guest-share',
                session.id,
                (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            )

            stored_file = store_dir / 'guest.txt'
            stored_file.write_text('private document', encoding='utf-8')
            document = document_repository.save_document(
                KnowledgeDocument(
                    user_id=guest.id,
                    filename='guest.txt',
                    content_type='text/plain',
                    storage_path=str(stored_file),
                )
            )
            chunk = DocumentChunk(document_id=document.id, chunk_index=0, content='private')
            document_repository.replace_document_index(
                document.id,
                [chunk],
                [DocumentChunkVector(
                    chunk_id=chunk.id,
                    document_id=document.id,
                    chunk_index=0,
                    vector=[1.0],
                )],
            )

            self.assertEqual(user_repository.cleanup_guest_users(days=7), 1)
            self.assertIsNone(user_repository.get_by_id(guest.id))
            self.assertIsNotNone(user_repository.get_by_id(regular.id))
            self.assertFalse(stored_file.exists())

            connection = sqlite3.connect(db_path)
            try:
                for table in (
                    'sessions',
                    'messages',
                    'share_tokens',
                    'documents',
                    'document_chunks',
                    'document_chunk_vectors',
                ):
                    count = connection.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
                    self.assertEqual(count, 0, table)
            finally:
                connection.close()


if __name__ == '__main__':
    unittest.main()
