import unittest
from fastapi import HTTPException

from app.api.routes.auth import RegisterRequest, register
from app.core.config import settings


class AuthCoreTestCase(unittest.TestCase):
    """认证核心功能测试"""

    def test_password_hashing(self):
        from app.core.auth import hash_password, verify_password

        password = 'test-password-123'
        hashed = hash_password(password)
        self.assertNotEqual(hashed, password)
        self.assertTrue(verify_password(password, hashed))
        self.assertFalse(verify_password('wrong-password', hashed))

    def test_jwt_token(self):
        from app.core.auth import create_access_token, decode_access_token

        data = {'sub': 'user-123', 'username': 'test'}
        token = create_access_token(data)
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 20)

        decoded = decode_access_token(token)
        self.assertIsNotNone(decoded)
        self.assertEqual(decoded['sub'], 'user-123')
        self.assertEqual(decoded['username'], 'test')

    def test_invalid_token(self):
        from app.core.auth import decode_access_token

        result = decode_access_token('invalid-token')
        self.assertIsNone(result)

    def test_registration_rejects_short_password(self):
        class UnusedRepository:
            pass

        with self.assertRaises(HTTPException) as raised:
            register(
                RegisterRequest(username='tester', password='short'),
                repo=UnusedRepository(),
            )
        self.assertEqual(raised.exception.status_code, 400)
        self.assertIn(str(settings.min_password_length), raised.exception.detail)


if __name__ == '__main__':
    unittest.main()
