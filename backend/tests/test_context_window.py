import unittest

from app.domain import ChatMessage
from app.services.context_window import build_context_window


class ContextWindowTestCase(unittest.TestCase):
    def test_short_history_is_unchanged(self):
        messages = [
            ChatMessage(session_id='s1', role='user', content='hello'),
            ChatMessage(session_id='s1', role='assistant', content='hi'),
        ]

        window = build_context_window(messages, 500, 10, 100)

        self.assertEqual(window.messages, messages)
        self.assertEqual(window.omitted_count, 0)

    def test_long_history_is_summarized_within_budget(self):
        messages = [
            ChatMessage(
                session_id='s1',
                role='user' if index % 2 == 0 else 'assistant',
                content=f'message {index} ' + ('detail ' * 120),
            )
            for index in range(20)
        ]

        window = build_context_window(messages, 300, 4, 80)

        self.assertLessEqual(window.estimated_tokens, 300)
        self.assertGreater(window.omitted_count, 0)
        self.assertEqual(window.messages[0].role, 'system')
        self.assertIn('Earlier conversation summary', window.messages[0].content)
        self.assertEqual(window.messages[-1].content, messages[-1].content)

    def test_single_oversized_message_is_truncated(self):
        message = ChatMessage(session_id='s1', role='user', content='important ' * 2000)

        window = build_context_window([message], 256, 4, 80)

        self.assertLessEqual(window.estimated_tokens, 256)
        self.assertEqual(window.messages[-1].role, 'user')
        self.assertIn('content truncated', window.messages[-1].content)


if __name__ == '__main__':
    unittest.main()
