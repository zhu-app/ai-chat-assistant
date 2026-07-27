import unittest

from app.core.config import settings, validate_runtime_settings


class SecurityConfigTestCase(unittest.TestCase):
    def test_production_rejects_default_jwt_secret(self):
        original_environment = settings.app_environment
        original_secret = settings.jwt_secret_key
        original_api_key = settings.openai_api_key
        try:
            settings.app_environment = 'production'
            settings.jwt_secret_key = 'change-me-to-a-random-string'
            settings.openai_api_key = 'configured'
            with self.assertRaises(RuntimeError):
                validate_runtime_settings()
        finally:
            settings.app_environment = original_environment
            settings.jwt_secret_key = original_secret
            settings.openai_api_key = original_api_key

    def test_llm_mock_disables_remote_provider_even_with_api_key(self):
        from app.llm.providers.openai_chat import OpenAICompatibleChatProvider

        original_api_key = settings.openai_api_key
        original_mock = settings.llm_mock
        try:
            settings.openai_api_key = 'configured'
            settings.llm_mock = True
            self.assertFalse(OpenAICompatibleChatProvider().has_remote_model)
        finally:
            settings.openai_api_key = original_api_key
            settings.llm_mock = original_mock


if __name__ == '__main__':
    unittest.main()
