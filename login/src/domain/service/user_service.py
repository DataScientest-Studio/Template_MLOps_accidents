import bcrypt

from domain import User, PasswordException, UserRepository, Role


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def authenticate_user(self, username: str, password: str) -> User:
        user: User = self.user_repository.get_user(username)
        if not bcrypt.checkpw(password.encode('utf-8'), user.hashed_password):
            raise PasswordException
        return user

    def add_user(self, username: str, password: str, role: Role) -> User:
        return self.user_repository.save_user(
            username,
            bcrypt.hashpw(
                password.encode('utf-8'),
                bcrypt.gensalt()
            ),
            role
        )
