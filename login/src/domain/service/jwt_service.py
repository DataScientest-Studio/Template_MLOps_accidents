from domain import Token, User, JwtRepository
from repository_jwt import JwtRepositoryImpl


class JwtService:
    jwt_repository: JwtRepository = JwtRepositoryImpl()

    def __init__(self, jwt_repository: JwtRepository):
        self.jwt_repository = jwt_repository

    def create_access_token(self, user: User) -> Token:
        return self.jwt_repository.create_access_token(user)

    def get_jwks(self) -> dict:
        return self.jwt_repository.get_jwks()
