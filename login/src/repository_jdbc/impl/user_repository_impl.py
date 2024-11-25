import os
from uuid import uuid4

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from domain import NotFoundException, UserRepository, Role, User
from repository_jdbc import RoleEntity, UserEntity

DATABASE_CONNECTION = os.environ.get('DATABASE_CONNECTION', 'postgresql://login:login@localhost:5432')

engine = create_engine(DATABASE_CONNECTION, echo=True)


class UserRepositoryImpl(UserRepository):

    def get_user(self, username: str) -> User:
        user = self.__find_by_username(username)
        if not user:
            raise NotFoundException()
        return self.__to_domain(user)

    def save_user(self, username: str, password_hashed: bytes, role: Role) -> User:
        with Session(engine) as session:
            spongebob = UserEntity(
                user_id=uuid4(),
                username=username,
                hashed_password=password_hashed,
                roles=[RoleEntity(role=role.value)],
            )
            session.add(spongebob)
            session.commit()
            return self.get_user(username)

    @staticmethod
    def __to_domain(user_entity: UserEntity) -> User:
        return User(
            user_id=user_entity.user_id,
            username=user_entity.username,
            hashed_password=bytes(user_entity.hashed_password),
            roles=[Role(user_entity.roles[0].role)],
        )

    @staticmethod
    def __find_by_username(username: str):
        with Session(engine) as session:
            session.expunge_all()
            stmt = (
                select(UserEntity)
                .where(UserEntity.username == username)
            )
            return session.scalars(stmt).unique().first()
