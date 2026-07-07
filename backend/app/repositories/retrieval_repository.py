from abc import ABC, abstractmethod

from app.domain import RetrievedChunk


class RetrievalRepository(ABC):
    @abstractmethod
    def retrieve(self, query: str, document_ids: list[str] | None = None) -> list[RetrievedChunk]: ...