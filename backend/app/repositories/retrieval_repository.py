from abc import ABC, abstractmethod

from app.domain import RetrievedChunk


class RetrievalRepository(ABC):
    @abstractmethod
    def retrieve(self, query: str, document_ids: list[str] | None = None) -> list[RetrievedChunk]: ...

    @property
    def embedding_mode(self) -> str:
        """返回当前 embedding 模式用于遥测。"""
        return 'unknown'