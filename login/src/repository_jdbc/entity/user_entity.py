from typing import List
from uuid import UUID

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserEntity(Base):
    __tablename__ = "user"

    user_id: Mapped[UUID] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[bytearray] = mapped_column(String(255))
    roles: Mapped[List["RoleEntity"]] = relationship(
        back_populates="user", cascade="all, delete-orphan",
        lazy="joined"
    )


class RoleEntity(Base):
    __tablename__ = "role"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.user_id"), primary_key=True)
    role: Mapped[str] = mapped_column(String(255))
    user: Mapped["UserEntity"] = relationship(back_populates="roles")
