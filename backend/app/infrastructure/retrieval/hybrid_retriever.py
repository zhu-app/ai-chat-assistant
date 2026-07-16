from app.domain import RetrievedChunk
from app.infrastructure.retrieval.local_file_retriever import LocalFileRetriever
from app.infrastructure.retrieval.vector_retriever import VectorRetriever
from app.repositories.document_repository import DocumentRepository
from app.repositories.retrieval_repository import RetrievalRepository
from app.infrastructure.retrieval.embedding_engine import EmbeddingEngine


class HybridRetriever(RetrievalRepository):
    def __init__(
        self,
        document_repository: DocumentRepository,
        embedding_engine: EmbeddingEngine,
        top_k: int = 4,
        vector_min_score: float = 0.12,
    ) -> None:
        self.top_k = top_k
        self._embedding_engine = embedding_engine
        # 无远程 embedding 时使用更低阈值
        if not embedding_engine.client:
            vector_min_score = 0.02
        self.vector_retriever = VectorRetriever(
            document_repository=document_repository,
            embedding_engine=embedding_engine,
            top_k=top_k,
            min_score=vector_min_score,
        )
        self.keyword_retriever = LocalFileRetriever(document_repository, top_k)

    @staticmethod
    def _chunk_key(chunk: RetrievedChunk) -> tuple[str, int]:
        return chunk.document_id, chunk.chunk_index

    def _merge(self, primary: list[RetrievedChunk], fallback: list[RetrievedChunk]) -> list[RetrievedChunk]:
        ordered: list[RetrievedChunk] = []
        seen: set[tuple[str, int]] = set()

        for chunk in [*primary, *fallback]:
            key = self._chunk_key(chunk)
            if key in seen:
                continue
            seen.add(key)
            ordered.append(chunk)
            if len(ordered) >= self.top_k:
                break

        return ordered

    def retrieve(self, query: str, document_ids: list[str] | None = None) -> list[RetrievedChunk]:
        vector_hits = self.vector_retriever.retrieve(query, document_ids)
        if len(vector_hits) >= self.top_k:
            return vector_hits

        keyword_hits = self.keyword_retriever.retrieve(query, document_ids)
        if not vector_hits:
            return keyword_hits

        return self._merge(vector_hits, keyword_hits)

    @property
    def embedding_mode(self) -> str:
        return 'hash_degraded' if self._embedding_engine.is_degraded else 'remote'