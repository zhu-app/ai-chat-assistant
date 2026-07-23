import asyncio
import sqlite3
import tempfile
import unittest
from pathlib import Path

from fastapi import UploadFile

from app.infrastructure.persistence.sqlite_document_repository import SqliteDocumentRepository
from app.services.document_service import DocumentService


class FakeEmbeddingEngine:
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(text)), 1.0] for text in texts]


class DocumentServiceTestCase(unittest.TestCase):
    def test_deferred_upload_can_be_indexed_and_retried(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repository = SqliteDocumentRepository(str(root / 'chat.db'))
            service = DocumentService(
                repository=repository,
                embedding_engine=FakeEmbeddingEngine(),
                store_dir=str(root / 'documents'),
                chunk_size=200,
                chunk_overlap=20,
            )
            try:
                upload = UploadFile(
                    filename='notes.txt',
                    file=open(root / 'upload.txt', 'w+b'),
                    headers={'content-type': 'text/plain'},
                )
                upload.file.write(b'alpha beta gamma ' * 50)
                upload.file.seek(0)

                documents = asyncio.run(
                    service.upload_documents([upload], user_id='owner', defer_indexing=True)
                )
                document = documents[0]
                self.assertEqual(document.status, 'uploaded')

                indexed = service.index_document(document.id)
                self.assertIsNotNone(indexed)
                self.assertEqual(indexed.status, 'ready')

                connection = sqlite3.connect(root / 'chat.db')
                try:
                    chunk_count = connection.execute(
                        'SELECT COUNT(*) FROM document_chunks WHERE document_id = ?',
                        (document.id,),
                    ).fetchone()[0]
                finally:
                    connection.close()
                self.assertGreater(chunk_count, 0)
                self.assertIsNone(service.retry_document(document.id, user_id='other-user'))
                repository.update_document_status(document.id, 'error')
                self.assertEqual(service.retry_document(document.id, user_id='owner').status, 'uploaded')
            finally:
                if 'upload' in locals():
                    upload.file.close()

    def test_index_claim_is_atomic(self):
        with tempfile.TemporaryDirectory() as tmp:
            repository = SqliteDocumentRepository(str(Path(tmp) / 'chat.db'))
            from app.domain import KnowledgeDocument

            document = KnowledgeDocument(
                filename='notes.txt',
                content_type='text/plain',
                storage_path=str(Path(tmp) / 'notes.txt'),
            )
            repository.save_document(document)

            self.assertIsNotNone(repository.claim_document_index(document.id))
            self.assertIsNone(repository.claim_document_index(document.id))


if __name__ == '__main__':
    unittest.main()
