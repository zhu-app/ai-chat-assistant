import asyncio
import unittest

from app.domain import SessionSettings
from app.infrastructure.persistence.memory_session_repository import InMemorySessionRepository
from app.infrastructure.retrieval.noop_retriever import NoopRetriever
from app.llm.providers.openai_chat import OpenAICompatibleChatProvider
from app.services.chat_service import ChatService
from app.services.session_service import SessionService


class ChatServiceTestCase(unittest.TestCase):
    def test_stream_chat_produces_standard_event_sequence(self):
        repository = InMemorySessionRepository()
        service = ChatService(
            session_service=SessionService(repository),
            session_repository=repository,
            provider=OpenAICompatibleChatProvider(),
            retriever=NoopRetriever(),
        )

        async def collect_events():
            events = []
            async for event in service.stream_chat(None, '你好，测试一下', SessionSettings()):
                events.append(event)
            return events

        events = asyncio.run(collect_events())
        event_types = [item['type'] for item in events]

        self.assertEqual(event_types[0], 'session_created')
        self.assertEqual(event_types[1], 'message_started')
        self.assertIn('token', event_types)
        # 最后两个事件：message_done 然后是 telemetry
        self.assertIn('message_done', event_types[-2:])
        self.assertIn('telemetry', event_types[-2:])


if __name__ == '__main__':
    unittest.main()