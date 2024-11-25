from uuid import UUID, uuid4

from pydantic import BaseModel, Field, conbytes

from domain import Role


class User(BaseModel):
    user_id: UUID = Field(default_factory=uuid4)
    username: str
    hashed_password: conbytes(strict=True, min_length=10, max_length=500)
    roles: list[Role]
