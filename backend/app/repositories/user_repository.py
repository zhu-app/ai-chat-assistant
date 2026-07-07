from abc import ABC, abstractmethod

from app.domain import User


class UserRepository(ABC):
    @abstractmethod
    def list_users(self) -> list[User]: ...

    @abstractmethod
    def get_by_username(self, username: str) -> User | None: ...

    @abstractmethod
    def get_by_id(self, user_id: str) -> User | None: ...

    @abstractmethod
    def create(self, username: str, hashed_password: str) -> User: ...