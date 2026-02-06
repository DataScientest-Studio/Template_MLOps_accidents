"""
FastAPI routes for the authentication service.
"""

import logging
from datetime import timedelta
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from services.common.auth import (
    authenticate_user,
    consume_password_reset_token,
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    create_user,
    delete_user,
    get_all_users,
    revoke_token,
    security,
    update_user_password,
    verify_token,
)
from services.common.auth_limits import (
    check_lockout,
    check_rate_limit,
    clear_failed_logins,
    record_failed_login,
    record_rate_limit_request,
)
from services.common.config import settings
from services.common.dependencies import ActiveUser, AdminUser
from services.common.models import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LoginResponse,
    ResetPasswordRequest,
    Token,
    TokenRefreshRequest,
    UserCreate,
    UserResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Authenticate user and return access token."""
    username = request.username

    # Per-username login rate limit
    if not check_rate_limit(
        username,
        settings.LOGIN_RATE_LIMIT_PER_USER,
        settings.LOGIN_RATE_WINDOW_SECONDS,
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts for this username. Try again later.",
        )

    # Account lockout after repeated failures
    locked, minutes_left = check_lockout(username)
    if locked:
        logger.warning("Login attempt for locked account: %s", username)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account temporarily locked. Try again after {minutes_left} minutes.",
        )

    user = authenticate_user(request.username, request.password)
    record_rate_limit_request(username, settings.LOGIN_RATE_WINDOW_SECONDS)

    if not user:
        record_failed_login(username)
        logger.info("Failed login for username: %s", username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    clear_failed_logins(username)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value},
        expires_delta=access_token_expires,
    )

    refresh_token = create_refresh_token(
        data={"sub": user.username, "role": user.role.value}
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=int(access_token_expires.total_seconds()),
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(request: TokenRefreshRequest):
    """Refresh an expired access token using a refresh token."""
    token_data = verify_token(request.refresh_token, token_type="refresh")
    username = token_data.username or ""

    if not check_rate_limit(
        username,
        settings.REFRESH_RATE_LIMIT_PER_USER,
        settings.REFRESH_RATE_WINDOW_SECONDS,
        key_prefix="refresh:",
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many refresh requests for this user. Try again later.",
        )

    record_rate_limit_request(
        username,
        settings.REFRESH_RATE_WINDOW_SECONDS,
        key_prefix="refresh:",
    )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={"sub": token_data.username, "role": token_data.role.value},
        expires_delta=access_token_expires,
    )

    return Token(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=int(access_token_expires.total_seconds()),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
):
    """Revoke the current access token (logout). Requires Bearer token."""
    revoke_token(credentials.credentials)
    return None


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: ActiveUser):
    """Get current authenticated user info."""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
    )


@router.get("/users", response_model=List[UserResponse])
async def list_users(current_user: AdminUser):
    """List all users (admin-only)."""
    all_users = get_all_users()
    return [
        UserResponse(
            id=u.id,
            username=u.username,
            email=u.email,
            full_name=u.full_name,
            role=u.role,
            is_active=u.is_active,
        )
        for u in all_users
    ]


@router.post("/users", response_model=UserResponse)
async def create_new_user(
    user_data: UserCreate,
    current_user: AdminUser,
):
    """Create a new user (admin-only)."""
    new_user = create_user(
        username=user_data.username,
        password=user_data.password,
        email=user_data.email,
        full_name=user_data.full_name,
        role=user_data.role,
    )

    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        full_name=new_user.full_name,
        role=new_user.role,
        is_active=new_user.is_active,
    )


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_by_id(user_id: int, current_user: AdminUser):
    """Delete a user by id (admin-only). Cannot delete the default admin."""
    deleted = delete_user(user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return None


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(request: ForgotPasswordRequest):
    """
    Request a password reset for the given username.
    In production, a reset link would be sent by email.
    When email is not configured, the reset token is returned (dev only).
    """
    token = create_password_reset_token(request.username)
    # Always return same message to avoid user enumeration
    if token and settings.DEV_PASSWORD_RESET_TOKEN_IN_RESPONSE:
        return ForgotPasswordResponse(
            message="If an account exists, a reset link has been sent.",
            reset_token=token,
        )
    return ForgotPasswordResponse(
        message="If an account exists, a reset link has been sent."
    )


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(request: ResetPasswordRequest):
    """Reset password using the token from forgot-password (or from email)."""
    username = consume_password_reset_token(request.token)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token.",
        )
    if not update_user_password(username, request.new_password):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password.",
        )
    return None
