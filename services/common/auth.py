"""
JWT Authentication and RBAC for MLOps microservices.

Provides:
- JWT token creation and verification
- Password hashing and verification
- FastAPI dependencies for authentication
- Role-based access control decorators
"""

import uuid
from datetime import datetime, timedelta
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import settings
from .models import TokenData, User, UserInDB, UserRole

# =============================================================================
# Password Hashing
# =============================================================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# =============================================================================
# OAuth2 / Bearer Token
# =============================================================================

# Using HTTPBearer for JWT Bearer token authentication
security = HTTPBearer(
    scheme_name="JWT",
    description="Enter your JWT token",
    auto_error=True,
)

optional_security = HTTPBearer(
    scheme_name="JWT",
    description="Enter your JWT token (optional)",
    auto_error=False,
)


# =============================================================================
# Password Functions
# =============================================================================


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password: The plain text password to verify
        hashed_password: The hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a plain password.

    Args:
        password: The plain text password to hash

    Returns:
        The hashed password
    """
    return pwd_context.hash(password)


# =============================================================================
# Token revocation (blocklist)
# =============================================================================

_revoked_tokens: set[str] = set()


def revoke_token(token: str) -> None:
    """Add token to revocation blocklist. Skips if token is already expired."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        exp = payload.get("exp")
        if exp and datetime.utcfromtimestamp(exp) <= datetime.utcnow():
            return  # Do not add expired tokens to blocklist
    except Exception:
        pass  # Invalid token: still add so it is never accepted
    _revoked_tokens.add(token)


def is_revoked(token: str) -> bool:
    """Return True if token has been revoked (e.g. after logout)."""
    return token in _revoked_tokens


# =============================================================================
# Token Functions
# =============================================================================


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary containing claims to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire, "type": "access", "jti": str(uuid.uuid4())})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def create_refresh_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT refresh token.

    Args:
        data: Dictionary containing claims to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire, "type": "refresh", "jti": str(uuid.uuid4())})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> TokenData:
    """
    Verify and decode a JWT token.

    Args:
        token: The JWT token string to verify
        token_type: Expected token type ("access" or "refresh")

    Returns:
        TokenData with decoded claims

    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if is_revoked(token):
        raise credentials_exception

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        # Check token type
        if payload.get("type") != token_type:
            raise credentials_exception

        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception

        role_str = payload.get("role", "user")
        role = UserRole(role_str) if role_str else UserRole.USER

        token_data = TokenData(
            username=username,
            role=role,
            exp=datetime.fromtimestamp(payload.get("exp", 0)),
        )
        return token_data

    except JWTError:
        raise credentials_exception


# =============================================================================
# User Database (in-memory or Postgres when DATABASE_URL is postgresql)
# =============================================================================

# In-memory user storage when not using Postgres
_fake_users_db: dict[str, UserInDB] = {}


def _use_postgres() -> bool:
    """True when DATABASE_URL is postgresql (sync driver)."""
    try:
        from services.common import database

        return database._is_postgres()
    except Exception:
        return False


def _db_row_to_user_in_db(row) -> UserInDB:
    """Convert UserModel row to UserInDB."""
    return UserInDB(
        id=row.id,
        username=row.username,
        email=row.email,
        full_name=row.full_name,
        role=UserRole(row.role) if isinstance(row.role, str) else row.role,
        is_active=bool(row.is_active),
        hashed_password=row.hashed_password,
        created_at=row.created_at or datetime.utcnow(),
        updated_at=row.updated_at,
    )


def _db_get_user(username: str) -> Optional[UserInDB]:
    """Get user from Postgres by username."""
    from sqlalchemy import select

    from services.common.database import UserModel, get_session

    with get_session() as session:
        row = (
            session.execute(select(UserModel).where(UserModel.username == username))
            .scalars()
            .one_or_none()
        )
        return _db_row_to_user_in_db(row) if row else None


def _db_create_user(
    username: str,
    password: str,
    email: Optional[str] = None,
    full_name: Optional[str] = None,
    role: UserRole = UserRole.USER,
) -> UserInDB:
    """Create user in Postgres."""
    from sqlalchemy import select

    from services.common.database import UserModel, get_session

    with get_session() as session:
        existing = (
            session.execute(select(UserModel).where(UserModel.username == username))
            .scalars()
            .one_or_none()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )
        user = UserModel(
            username=username,
            email=email,
            full_name=full_name,
            role=role.value,
            is_active=1,
            hashed_password=get_password_hash(password),
        )
        session.add(user)
        session.flush()
        return _db_row_to_user_in_db(user)


def _db_ensure_admin() -> None:
    """Ensure default admin user exists in Postgres."""
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    from services.common.database import (
        UserModel,
        create_tables_if_postgres,
        get_session,
    )

    create_tables_if_postgres()
    with get_session() as session:
        stmt = (
            pg_insert(UserModel)
            .values(
                username=settings.ADMIN_USERNAME,
                email=settings.ADMIN_EMAIL,
                full_name="Administrator",
                role=UserRole.ADMIN.value,
                is_active=1,
                hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
            )
            .on_conflict_do_nothing(index_elements=[UserModel.username])
        )
        session.execute(stmt)


def _init_admin_user():
    """Initialize the default admin user (in-memory or Postgres). Skipped if admin credentials not set in env."""
    if not (settings.ADMIN_USERNAME and settings.ADMIN_PASSWORD):
        return
    if _use_postgres():
        _db_ensure_admin()
        return
    if settings.ADMIN_USERNAME not in _fake_users_db:
        _fake_users_db[settings.ADMIN_USERNAME] = UserInDB(
            id=1,
            username=settings.ADMIN_USERNAME,
            email=settings.ADMIN_EMAIL,
            full_name="Administrator",
            role=UserRole.ADMIN,
            is_active=True,
            hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
            created_at=datetime.utcnow(),
        )


# Initialize admin on module load
_init_admin_user()


def get_user(username: str) -> Optional[UserInDB]:
    """
    Get a user from the database.

    Args:
        username: The username to look up

    Returns:
        UserInDB if found, None otherwise
    """
    if _use_postgres():
        return _db_get_user(username)
    return _fake_users_db.get(username)


def create_user(
    username: str,
    password: str,
    email: Optional[str] = None,
    full_name: Optional[str] = None,
    role: UserRole = UserRole.USER,
) -> UserInDB:
    """
    Create a new user.

    Args:
        username: The username for the new user
        password: The plain text password
        email: Optional email address
        full_name: Optional full name
        role: User role (default: USER)

    Returns:
        The created UserInDB instance

    Raises:
        HTTPException: If username already exists
    """
    if _use_postgres():
        return _db_create_user(username, password, email, full_name, role)
    if username in _fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    user_id = len(_fake_users_db) + 1
    user = UserInDB(
        id=user_id,
        username=username,
        email=email,
        full_name=full_name,
        role=role,
        is_active=True,
        hashed_password=get_password_hash(password),
        created_at=datetime.utcnow(),
    )
    _fake_users_db[username] = user
    return user


def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """
    Authenticate a user with username and password.

    Args:
        username: The username to authenticate
        password: The plain text password

    Returns:
        UserInDB if authentication succeeds, None otherwise
    """
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


# =============================================================================
# FastAPI Dependencies
# =============================================================================


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> User:
    """
    FastAPI dependency to get the current authenticated user.

    Validates JWT token and returns User. If user doesn't exist in local database,
    creates a User object from token data (for microservices where user data
    is only stored in auth service).

    Args:
        credentials: Bearer token from request header

    Returns:
        Current authenticated User

    Raises:
        HTTPException: If token is invalid
    """
    token_data = verify_token(credentials.credentials)

    # Try to get user from local database first
    user = get_user(token_data.username)
    if user is not None:
        # User exists locally, return full user data
        return User(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    # User doesn't exist locally (created in auth service, not synced here)
    # Create User from token data - token is already validated, so we trust it
    return User(
        id=0,  # Placeholder ID - not used for authorization
        username=token_data.username,
        email=None,  # Not in token
        full_name=None,  # Not in token
        role=token_data.role,
        is_active=True,  # Assume active if token is valid
        created_at=datetime.utcnow(),  # Placeholder
        updated_at=None,
    )


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    FastAPI dependency to get the current active user.

    Args:
        current_user: User from get_current_user dependency

    Returns:
        Current active User

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


async def get_optional_user(
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials], Depends(optional_security)
    ],
) -> Optional[User]:
    """
    FastAPI dependency to optionally get the current user.

    Args:
        credentials: Optional Bearer token from request header

    Returns:
        User if authenticated, None otherwise
    """
    if credentials is None:
        return None

    try:
        token_data = verify_token(credentials.credentials)
        user = get_user(token_data.username)
        if user:
            return User(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )
    except HTTPException:
        pass

    return None


# =============================================================================
# Role-Based Access Control Dependencies
# =============================================================================


async def require_admin(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """
    FastAPI dependency that requires admin role.

    Args:
        current_user: Active user from get_current_active_user

    Returns:
        User if admin

    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


async def require_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """
    FastAPI dependency that requires at least user role.

    Args:
        current_user: Active user from get_current_active_user

    Returns:
        User (any authenticated active user)
    """
    return current_user


# =============================================================================
# Utility Functions
# =============================================================================


def check_permission(user: User, required_role: UserRole) -> bool:
    """
    Check if a user has the required role or higher.

    Args:
        user: The user to check
        required_role: The minimum required role

    Returns:
        True if user has permission, False otherwise
    """
    role_hierarchy = {
        UserRole.USER: 0,
        UserRole.ADMIN: 1,
    }

    return role_hierarchy.get(user.role, 0) >= role_hierarchy.get(required_role, 0)


def _db_get_user_by_id(user_id: int) -> Optional[UserInDB]:
    """Get user from Postgres by id."""
    from services.common.database import UserModel, get_session

    with get_session() as session:
        row = session.get(UserModel, user_id)
        return _db_row_to_user_in_db(row) if row else None


def _db_update_user_password(username: str, new_hashed_password: str) -> bool:
    """Update user password in Postgres by username. Returns True if updated."""
    from sqlalchemy import update

    from services.common.database import UserModel, get_session

    with get_session() as session:
        result = session.execute(
            update(UserModel)
            .where(UserModel.username == username)
            .values(hashed_password=new_hashed_password)
        )
        return result.rowcount > 0


def _db_delete_user(user_id: int) -> bool:
    """Delete user from Postgres by id. Raises HTTPException if admin."""
    from services.common.database import UserModel, get_session

    with get_session() as session:
        row = session.get(UserModel, user_id)
        if not row:
            return False
        if row.username == settings.ADMIN_USERNAME:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete the default admin user",
            )
        session.delete(row)
        session.flush()
        return True


def _db_get_all_users() -> list[User]:
    """Get all users from Postgres."""
    from sqlalchemy import select

    from services.common.database import UserModel, get_session

    with get_session() as session:
        rows = session.execute(select(UserModel)).scalars().all()
        return [
            User(
                id=r.id,
                username=r.username,
                email=r.email,
                full_name=r.full_name,
                role=UserRole(r.role) if isinstance(r.role, str) else r.role,
                is_active=bool(r.is_active),
                created_at=r.created_at or datetime.utcnow(),
                updated_at=r.updated_at,
            )
            for r in rows
        ]


def get_user_by_id(user_id: int) -> Optional[UserInDB]:
    """
    Get a user by id (admin function).

    Args:
        user_id: The user id to look up

    Returns:
        UserInDB if found, None otherwise
    """
    if _use_postgres():
        return _db_get_user_by_id(user_id)
    for u in _fake_users_db.values():
        if u.id == user_id:
            return u
    return None


def delete_user(user_id: int) -> bool:
    """
    Delete a user by id (admin-only). Cannot delete the default admin.

    Args:
        user_id: The user id to delete

    Returns:
        True if user was deleted, False if not found

    Raises:
        HTTPException: If trying to delete the default admin user
    """
    if _use_postgres():
        return _db_delete_user(user_id)
    user = get_user_by_id(user_id)
    if not user:
        return False
    if user.username == settings.ADMIN_USERNAME:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete the default admin user",
        )
    del _fake_users_db[user.username]
    return True


def get_all_users() -> list[User]:
    """
    Get all users (admin function).

    Returns:
        List of all users
    """
    if _use_postgres():
        return _db_get_all_users()
    return [
        User(
            id=u.id,
            username=u.username,
            email=u.email,
            full_name=u.full_name,
            role=u.role,
            is_active=u.is_active,
            created_at=u.created_at,
            updated_at=u.updated_at,
        )
        for u in _fake_users_db.values()
    ]


# =============================================================================
# Password reset (token-based, in-memory store)
# =============================================================================

# reset_token -> (username, expires_at)
_password_reset_tokens: dict[str, tuple[str, datetime]] = {}
_RESET_TOKEN_EXPIRE_MINUTES = 60


def create_password_reset_token(username: str) -> Optional[str]:
    """
    Create a one-time password reset token for the user.
    Returns the token string, or None if user not found.
    """
    user = get_user(username)
    if not user:
        return None
    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(minutes=_RESET_TOKEN_EXPIRE_MINUTES)
    _password_reset_tokens[token] = (username, expires_at)
    return token


def consume_password_reset_token(token: str) -> Optional[str]:
    """
    Validate reset token and return username if valid. Token is consumed (removed).
    Returns None if token invalid or expired.
    """
    if not token or token not in _password_reset_tokens:
        return None
    username, expires_at = _password_reset_tokens.pop(token)
    if expires_at < datetime.utcnow():
        return None
    return username


def update_user_password(username: str, new_password: str) -> bool:
    """
    Set a new password for the user (by username).
    Returns True if updated.
    """
    hashed = get_password_hash(new_password)
    if _use_postgres():
        return _db_update_user_password(username, hashed)
    if username not in _fake_users_db:
        return False
    _fake_users_db[username].hashed_password = hashed
    return True
