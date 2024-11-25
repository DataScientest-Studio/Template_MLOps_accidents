from abc import ABC, abstractmethod

from domain import User, Token


class JwtRepository(ABC):

    @abstractmethod
    def create_access_token(self, username: User) -> Token:
        pass

    @abstractmethod
    def get_jwks(self) -> dict:
        pass
