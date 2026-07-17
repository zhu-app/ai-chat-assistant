import re
import sqlite3

from app.domain import RetrievedChunk
from app.repositories.document_repository import DocumentRepository
from app.repositories.retrieval_repository import RetrievalRepository


class LocalFileRetriever(RetrievalRepository):
    def __init__(self, document_repository: DocumentRepository, top_k: int = 4) -> None:
        self.document_repository = document_repository
        self.top_k = top_k
        self.db_path = getattr(document_repository, 'db_path', None)

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r'\s+', ' ', text).strip().lower()

    @classmethod
    def _extract_query_terms(cls, query: str) -> list[str]:
        normalized = cls._normalize(query)
        if not normalized:
            return []

        english_terms = re.findall(r'[a-z0-9_\-]{2,}', normalized)
        cjk_chars = re.findall(r'[\u4e00-\u9fff]', normalized)
        compact_cjk = ''.join(cjk_chars)

        cjk_terms: list[str] = []
        if compact_cjk:
            cjk_terms.append(compact_cjk)
            cjk_terms.extend(
                compact_cjk[index : index + 2]
                for index in range(len(compact_cjk) - 1)
                if len(compact_cjk[index : index + 2]) == 2
            )

        ordered_terms: list[str] = []
        for term in [*english_terms, *cjk_terms]:
            if term and term not in ordered_terms:
                ordered_terms.append(term)
        return ordered_terms

    @classmethod
    def _score_row(cls, query_terms: list[str], filename: str, content: str) -> int:
        haystack = cls._normalize(f'{filename}\n{content}')
        compact_haystack = re.sub(r'\s+', '', haystack)
        score = 0

        for term in query_terms:
            if not term:
                continue
            if re.fullmatch(r'[\u4e00-\u9fff]+', term):
                if term in compact_haystack:
                    score += max(len(term), 2)
            elif term in haystack:
                score += 2

        return score

    @staticmethod
    def _to_chunk(row: sqlite3.Row, score: int) -> RetrievedChunk:
        return RetrievedChunk(
            document_id=row['document_id'],
            filename=row['filename'],
            content=row['content'][:1200].strip(),
            score=score,
            chunk_index=row['chunk_index'],
        )

    def retrieve(self, query: str, document_ids: list[str] | None = None) -> list[RetrievedChunk]:
        if not self.db_path:
            return []

        # 空列表 = 用户没选文档，不搜索任何文档
        if document_ids is not None and not document_ids:
            return []

        query_terms = self._extract_query_terms(query)
        if not query_terms and not document_ids:
            return []

        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                '''
                SELECT dc.document_id, d.filename, dc.content, dc.chunk_index
                FROM document_chunks dc
                JOIN documents d ON d.id = dc.document_id
                WHERE d.status = 'ready'
                ORDER BY d.created_at DESC, dc.chunk_index ASC
                '''
            ).fetchall()

        filtered_rows = [row for row in rows if document_ids is None or row['document_id'] in document_ids]
        if not filtered_rows:
            return []

        matches: list[RetrievedChunk] = []
        for row in filtered_rows:
            score = self._score_row(query_terms, row['filename'], row['content'])
            if score <= 0:
                continue
            matches.append(self._to_chunk(row, score))

        if matches:
            matches.sort(key=lambda item: item.score, reverse=True)
            return matches[: self.top_k]

        if document_ids:
            fallback_rows = filtered_rows[: self.top_k]
            return [self._to_chunk(row, 1) for row in fallback_rows]

        return []