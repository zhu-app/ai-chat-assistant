import asyncio
import unittest

from fastapi import HTTPException

from app.api.routes.chat import chat_stream
from app.api.schemas.chat import ChatStreamRequest, SessionSettingsDto
from app.domain import KnowledgeDocument


class FakeDocumentService:
    def __init__(self, documents=None):
        self.documents = documents or []

    def list_documents(self, user_id: str):
        return self.documents


class ChatRouteSecurityTestCase(unittest.TestCase):
    def test_rag_rejects_document_owned_by_another_user(self):
        payload = ChatStreamRequest(
            message='question',
            settings=SessionSettingsDto(useRag=True, documentIds=['other-document']),
        )

        with self.assertRaises(HTTPException) as raised:
            asyncio.run(
                chat_stream(
                    payload=payload,
                    request=None,
                    chat_service=None,
                    document_service=FakeDocumentService(),
                    user_id='user-1',
                )
            )
        self.assertEqual(raised.exception.status_code, 403)

    def test_rag_rejects_document_that_is_still_processing(self):
        document = KnowledgeDocument(
            id='document-1',
            user_id='user-1',
            filename='notes.txt',
            content_type='text/plain',
            storage_path='unused',
            status='processing',
        )
        payload = ChatStreamRequest(
            message='question',
            settings=SessionSettingsDto(useRag=True, documentIds=[document.id]),
        )

        with self.assertRaises(HTTPException) as raised:
            asyncio.run(
                chat_stream(
                    payload=payload,
                    request=None,
                    chat_service=None,
                    document_service=FakeDocumentService([document]),
                    user_id='user-1',
                )
            )
        self.assertEqual(raised.exception.status_code, 409)


if __name__ == '__main__':
    unittest.main()
