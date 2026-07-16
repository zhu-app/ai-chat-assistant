import json
import sqlite3
from typing import Any

from app.domain import RetrievedChunk
from app.infrastructure.retrieval.embedding_engine import EmbeddingEngine
from app.repositories.document_repository import DocumentRepository
from app.repositories.retrieval_repository import RetrievalRepository


class VectorRetriever(RetrievalRepository):
    def __init__(
        self,
        document_repository: DocumentRepository,
        embedding_engine: EmbeddingEngine,
        top_k: int = 4,
        min_score: float = 0.12,
    ) -> None:
        self.document_repository = document_repository
        self.embedding_engine = embedding_engine
        self.top_k = top_k
        # 无远程 embedding 时（哈希降级），余弦相似度普遍很低，使用更低的阈值
        if not embedding_engine.client:
            min_score = 0.02
        self.min_score = min_score
        self.db_path = getattr(document_repository, 'db_path', None)

    @staticmethod
    def _to_chunk(row: sqlite3.Row, score: float) -> RetrievedChunk:
        return RetrievedChunk(
            document_id=row['document_id'],
            filename=row['filename'],
            content=row['content'][:1200].strip(),
            score=max(int(score * 100), 1),
            chunk_index=row['chunk_index'],
        )

    def retrieve(self, query: str, document_ids: list[str] | None = None) -> list[RetrievedChunk]:
        if not self.db_path:
            return []

        query_vector = self.embedding_engine.embed_query(query)
        if not any(query_vector):
            return []

        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            connection.execute('PRAGMA journal_mode=WAL')
            # 将 document_ids 过滤下推到 SQL 层，避免全表扫描
            if document_ids:
                placeholders = ','.join('?' * len(document_ids))
                params: list[Any] = document_ids
                rows = connection.execute(
                    f'''
                    SELECT dc.document_id, d.filename, dc.content, dc.chunk_index, dcv.vector_json
                    FROM document_chunk_vectors dcv
                    JOIN document_chunks dc ON dc.id = dcv.chunk_id
                    JOIN documents d ON d.id = dc.document_id
                    WHERE d.status = 'ready' AND dc.document_id IN ({placeholders})
                    ORDER BY d.created_at DESC, dc.chunk_index ASC
                    ''',
                    params,
                ).fetchall()
            else:
                rows = connection.execute(
                    '''
                    SELECT dc.document_id, d.filename, dc.content, dc.chunk_index, dcv.vector_json
                    FROM document_chunk_vectors dcv
                    JOIN document_chunks dc ON dc.id = dcv.chunk_id
                    JOIN documents d ON d.id = dc.document_id
                    WHERE d.status = 'ready'
                    ORDER BY d.created_at DESC, dc.chunk_index ASC
                    '''
                ).fetchall()

        # 注：document_ids 为空时不过滤（返回所有文档结果）
        filtered_rows = rows if not document_ids else rows
        if not filtered_rows:
            return []

        scored_rows: list[tuple[float, sqlite3.Row]] = []
        for row in filtered_rows:
            vector = json.loads(row['vector_json'])
            score = self.embedding_engine.cosine_similarity(query_vector, vector)
            if score < self.min_score:
                continue
            scored_rows.append((score, row))

        if not scored_rows:
            return []

        scored_rows.sort(key=lambda item: item[0], reverse=True)
        return [self._to_chunk(row, score) for score, row in scored_rows[: self.top_k]]