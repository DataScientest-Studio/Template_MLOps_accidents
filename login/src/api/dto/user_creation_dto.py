from pydantic import BaseModel


class UserCreationDto(BaseModel):
    username: str
    password: str
