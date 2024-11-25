from abc import ABC, abstractmethod

from domain import User, Role


class UserRepository(ABC):

    @abstractmethod
    def get_user(self, username: str) -> User:
        pass

    @abstractmethod
    def save_user(self, username: str, password_hashed: bytes, role: Role) -> User:
        pass
