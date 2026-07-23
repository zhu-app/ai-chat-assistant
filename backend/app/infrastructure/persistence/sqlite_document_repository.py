import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from app.domain import DocumentChunk, DocumentChunkVector, KnowledgeDocument
from app.repositories.document_repository import DocumentRepository


class SqliteDocumentRepository(DocumentRepository):
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
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
            connection.executescript(
                '''
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL DEFAULT '',
                    filename TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    storage_path TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS document_chunks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS document_chunk_vectors (
                    chunk_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    vector_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE,
                    FOREIGN KEY(chunk_id) REFERENCES document_chunks(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_chunk_vectors_doc_id ON document_chunk_vectors(document_id);
                CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON document_chunks(document_id);
                '''
            )
            # 兼容旧表
            try:
                connection.execute('ALTER TABLE documents ADD COLUMN user_id TEXT NOT NULL DEFAULT \'\'')
            except Exception:
                pass

    @staticmethod
    def _to_document(row: sqlite3.Row) -> KnowledgeDocument:
        return KnowledgeDocument(
            id=row['id'],
            user_id=str(row['user_id']) if 'user_id' in row.keys() else '',
            filename=row['filename'],
            content_type=row['content_type'],
            storage_path=row['storage_path'],
            status=row['status'],
            created_at=row['created_at'],
        )

    def list_documents(self, user_id: str | None = None) -> list[KnowledgeDocument]:
        with self._connect() as connection:
            if user_id:
                rows = connection.execute(
                    'SELECT * FROM documents WHERE user_id = ? ORDER BY created_at DESC', (user_id,)
                ).fetchall()
            else:
                rows = connection.execute('SELECT * FROM documents ORDER BY created_at DESC').fetchall()
        return [self._to_document(row) for row in rows]

    def get_document(self, document_id: str) -> KnowledgeDocument | None:
        with self._connect() as connection:
            row = connection.execute('SELECT * FROM documents WHERE id = ?', (document_id,)).fetchone()
        return self._to_document(row) if row else None

    def save_document(self, document: KnowledgeDocument) -> KnowledgeDocument:
        with self._connect() as connection:
            connection.execute(
                'INSERT INTO documents (id, user_id, filename, content_type, storage_path, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (
                    document.id,
                    document.user_id,
                    document.filename,
                    document.content_type,
                    document.storage_path,
                    document.status,
                    document.created_at,
                ),
            )
        return document

    def update_document_status(self, document_id: str, status: str) -> KnowledgeDocument | None:
        with self._connect() as connection:
            connection.execute('UPDATE documents SET status = ? WHERE id = ?', (status, document_id))
        return self.get_document(document_id)

    def claim_document_index(self, document_id: str) -> KnowledgeDocument | None:
        with self._connect() as connection:
            connection.execute('BEGIN IMMEDIATE')
            cursor = connection.execute(
                """UPDATE documents SET status = 'processing'
                   WHERE id = ? AND status IN ('uploaded', 'error')""",
                (document_id,),
            )
            if cursor.rowcount != 1:
                return None
            row = connection.execute(
                'SELECT * FROM documents WHERE id = ?',
                (document_id,),
            ).fetchone()
        return self._to_document(row) if row else None

    def replace_document_index(
        self,
        document_id: str,
        chunks: list[DocumentChunk],
        vectors: list[DocumentChunkVector],
    ) -> None:
        with self._connect() as connection:
            connection.execute('BEGIN IMMEDIATE')
            exists = connection.execute(
                'SELECT 1 FROM documents WHERE id = ?',
                (document_id,),
            ).fetchone()
            if not exists:
                raise LookupError('Document was deleted while indexing')
            connection.execute(
                'DELETE FROM document_chunk_vectors WHERE document_id = ?',
                (document_id,),
            )
            connection.execute(
                'DELETE FROM document_chunks WHERE document_id = ?',
                (document_id,),
            )
            connection.executemany(
                'INSERT INTO document_chunks (id, document_id, chunk_index, content, created_at) VALUES (?, ?, ?, ?, ?)',
                [
                    (chunk.id, chunk.document_id, chunk.chunk_index, chunk.content, chunk.created_at)
                    for chunk in chunks
                ],
            )
            connection.executemany(
                'INSERT INTO document_chunk_vectors (chunk_id, document_id, chunk_index, vector_json, created_at) VALUES (?, ?, ?, ?, ?)',
                [
                    (
                        vector.chunk_id,
                        vector.document_id,
                        vector.chunk_index,
                        json.dumps(vector.vector),
                        vector.created_at,
                    )
                    for vector in vectors
                ],
            )

    def save_chunks(self, chunks: list[DocumentChunk]) -> None:
        if not chunks:
            return
        with self._connect() as connection:
            connection.executemany(
                'INSERT INTO document_chunks (id, document_id, chunk_index, content, created_at) VALUES (?, ?, ?, ?, ?)',
                [
                    (
                        chunk.id,
                        chunk.document_id,
                        chunk.chunk_index,
                        chunk.content,
                        chunk.created_at,
                    )
                    for chunk in chunks
                ],
            )

    def save_chunk_vectors(self, vectors: list[DocumentChunkVector]) -> None:
        if not vectors:
            return
        with self._connect() as connection:
            connection.executemany(
                'INSERT OR REPLACE INTO document_chunk_vectors (chunk_id, document_id, chunk_index, vector_json, created_at) VALUES (?, ?, ?, ?, ?)',
                [
                    (
                        vector.chunk_id,
                        vector.document_id,
                        vector.chunk_index,
                        json.dumps(vector.vector),
                        vector.created_at,
                    )
                    for vector in vectors
                ],
            )

    def clear_document_index(self, document_id: str) -> None:
        with self._connect() as connection:
            connection.execute('DELETE FROM document_chunk_vectors WHERE document_id = ?', (document_id,))
            connection.execute('DELETE FROM document_chunks WHERE document_id = ?', (document_id,))

    def delete_document(self, document_id: str) -> KnowledgeDocument | None:
        document = self.get_document(document_id)
        if not document:
            return None
        with self._connect() as connection:
            connection.execute('DELETE FROM document_chunk_vectors WHERE document_id = ?', (document_id,))
            connection.execute('DELETE FROM document_chunks WHERE document_id = ?', (document_id,))
            connection.execute('DELETE FROM documents WHERE id = ?', (document_id,))
        return document
