from app.repositories.retrieval_repository import RetrievalRepository


class NoopRetriever(RetrievalRepository):
    def retrieve(self, query: str, document_ids: list[str] | None = None):
        return []