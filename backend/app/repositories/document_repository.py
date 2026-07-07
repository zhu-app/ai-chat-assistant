from abc import ABC, abstractmethod

from app.domain import DocumentChunk, DocumentChunkVector, KnowledgeDocument


class DocumentRepository(ABC):
    @abstractmethod
    def list_documents(self, user_id: str | None = None) -> list[KnowledgeDocument]: ...

    @abstractmethod
    def get_document(self, document_id: str) -> KnowledgeDocument | None: ...

    @abstractmethod
    def save_document(self, document: KnowledgeDocument) -> KnowledgeDocument: ...

    @abstractmethod
    def update_document_status(self, document_id: str, status: str) -> KnowledgeDocument | None: ...

    @abstractmethod
    def save_chunks(self, chunks: list[DocumentChunk]) -> None: ...

    @abstractmethod
    def save_chunk_vectors(self, vectors: list[DocumentChunkVector]) -> None: ...

    @abstractmethod
    def delete_document(self, document_id: str) -> KnowledgeDocument | None: ...