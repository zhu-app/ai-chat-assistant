import logging
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings
from app.domain import DocumentChunk, DocumentChunkVector, KnowledgeDocument
from app.infrastructure.parsers.registry import extract_text_from_upload, is_supported_document
from app.infrastructure.retrieval.embedding_engine import EmbeddingEngine
from app.repositories.document_repository import DocumentRepository

logger = logging.getLogger(__name__)


class DocumentValidationError(ValueError):
    pass


class DocumentService:
    def __init__(
        self,
        repository: DocumentRepository,
        embedding_engine: EmbeddingEngine,
        store_dir: str,
        chunk_size: int,
        chunk_overlap: int,
    ) -> None:
        self.repository = repository
        self.embedding_engine = embedding_engine
        self.store_dir = Path(store_dir)
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.chunk_size = max(chunk_size, 200)
        self.chunk_overlap = max(min(chunk_overlap, self.chunk_size - 1), 0)

    def list_documents(self, user_id: str | None = None) -> list[KnowledgeDocument]:
        return self.repository.list_documents(user_id=user_id)

    async def upload_documents(self, files: list[UploadFile], user_id: str = '') -> list[KnowledgeDocument]:
        documents: list[KnowledgeDocument] = []
        for file in files:
            document = await self._store_document(file, user_id=user_id)
            documents.append(document)
        return documents

    def delete_document(self, document_id: str, user_id: str = '') -> KnowledgeDocument | None:
        document = self.repository.get_document(document_id)
        if not document:
            return None
        # 非自己的文档不能删除（除非是旧版无归属文档）
        if document.user_id and document.user_id != user_id:
            return None
        self.repository.delete_document(document_id)
        path = Path(document.storage_path)
        if path.exists():
            path.unlink()
        return document

    async def _store_document(self, file: UploadFile, user_id: str = '') -> KnowledgeDocument:
        original_name = file.filename or 'unnamed.txt'
        self._validate_upload(original_name)

        suffix = Path(original_name).suffix or '.txt'
        stored_name = f'{uuid4()}{suffix}'
        storage_path = self.store_dir / stored_name
        content = await file.read()
        self._validate_upload_content(original_name, content)
        storage_path.write_bytes(content)

        document = KnowledgeDocument(
            user_id=user_id,
            filename=original_name,
            content_type=file.content_type or 'application/octet-stream',
            storage_path=str(storage_path),
            status='uploaded',
        )
        self.repository.save_document(document)
        self.repository.update_document_status(document.id, 'processing')

        try:
            extracted_text = extract_text_from_upload(document.filename, document.content_type, storage_path)
            chunks = [
                DocumentChunk(document_id=document.id, chunk_index=index, content=chunk)
                for index, chunk in enumerate(self._chunk_text(extracted_text))
            ]
            self.repository.save_chunks(chunks)

            vectors = [
                DocumentChunkVector(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    chunk_index=chunk.chunk_index,
                    vector=vector,
                )
                for chunk, vector in zip(chunks, self.embedding_engine.embed_documents([chunk.content for chunk in chunks]))
            ]
            self.repository.save_chunk_vectors(vectors)
            logger.info('document indexed', extra={'document_id': document.id, 'filename': document.filename, 'chunks': len(chunks)})
            return self.repository.update_document_status(document.id, 'ready') or document
        except Exception:
            self.repository.update_document_status(document.id, 'error')
            logger.exception('document indexing failed', extra={'document_id': document.id, 'filename': document.filename})
            if storage_path.exists():
                storage_path.unlink()
            raise

    def _validate_upload(self, filename: str) -> None:
        if not is_supported_document(filename, settings.allowed_document_extensions):
            allowed = ', '.join(settings.allowed_document_extensions)
            raise DocumentValidationError(f'仅支持以下文档类型: {allowed}')

    def _validate_upload_content(self, filename: str, content: bytes) -> None:
        if not content:
            raise DocumentValidationError(f'文档不能为空: {filename}')
        if len(content) > settings.max_upload_bytes:
            raise DocumentValidationError(
                f'文档超过大小限制，单文件最大 {settings.max_upload_bytes // (1024 * 1024)}MB: {filename}'
            )

    def _chunk_text(self, text: str) -> Iterable[str]:
        normalized = '\n'.join(line.rstrip() for line in text.splitlines()).strip()
        if not normalized:
            return []

        chunks: list[str] = []
        start = 0
        total = len(normalized)
        while start < total:
            end = min(total, start + self.chunk_size)
            chunk = normalized[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= total:
                break
            start = max(end - self.chunk_overlap, start + 1)
        return chunks