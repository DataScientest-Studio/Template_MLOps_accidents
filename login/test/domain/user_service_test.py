import os
import sys
import uuid

import pytest

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../../src")

from unittest.mock import MagicMock

from domain import NotFoundException, Role, UserService, User, PasswordException
from repository_jdbc import UserRepositoryImpl


@pytest.fixture
def default_user():
    return User(
        user_id=uuid.uuid4(),
        username='username_test',
        hashed_password=b'$2b$12$f0a11.s9LufjdgSidlQwS.He3/1iOXG2z4AarDaIgRHEmiX7X5zrS',
        roles=[Role('ADMIN')],
    )


def test_authenticate_user(default_user):
    # Given
    mock = UserRepositoryImpl()
    mock.get_user = MagicMock(return_value=default_user)
    service = UserService(mock)
    # When
    user_authenticate = service.authenticate_user('username_test', 'admin')
    # Then
    assert user_authenticate == default_user


def test_authenticate_user_wrong_password(default_user):
    # Given
    mock = UserRepositoryImpl()
    mock.get_user = MagicMock(return_value=default_user)
    service = UserService(mock)
    # Then
    with pytest.raises(PasswordException) as exc_info:
        # When
        service.authenticate_user('username_test', 'admin2')
    assert str(exc_info.value) == ''


def test_authenticate_user_not_exists():
    # Given
    mock = UserRepositoryImpl()
    mock.get_user = MagicMock(side_effect=NotFoundException)
    service = UserService(mock)
    # Then
    with pytest.raises(NotFoundException) as exc_info:
        # When
        service.authenticate_user('username_test', 'admin')
    assert str(exc_info.value) == ''
