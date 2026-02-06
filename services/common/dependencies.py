"""
FastAPI dependencies for MLOps microservices.

Provides reusable dependencies for:
- Authentication
- Database sessions (future)
- Service clients
- Common utilities
"""

from typing import Annotated, Any, Dict

from fastapi import Depends, Header, HTTPException, Query, status

from .auth import (
    get_current_active_user,
    get_current_user,
    get_optional_user,
    require_admin,
    require_user,
)
from .config import Settings, get_settings
from .models import User, UserRole

# =============================================================================
# Re-export Auth Dependencies
# =============================================================================

# These are the main authentication dependencies to use in routes
CurrentUser = Annotated[User, Depends(get_current_user)]
ActiveUser = Annotated[User, Depends(get_current_active_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]
AdminUser = Annotated[User, Depends(require_admin)]
AuthenticatedUser = Annotated[User, Depends(require_user)]

# =============================================================================
# Settings Dependency
# =============================================================================

SettingsDep = Annotated[Settings, Depends(get_settings)]


# =============================================================================
# Common Query Parameters
# =============================================================================


async def pagination_params(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
) -> Dict[str, int]:
    """
    Common pagination parameters.

    Args:
        skip: Number of items to skip (offset)
        limit: Maximum number of items to return

    Returns:
        Dictionary with skip and limit values
    """
    return {"skip": skip, "limit": limit}


PaginationParams = Annotated[Dict[str, int], Depends(pagination_params)]


# =============================================================================
# Request ID Tracking
# =============================================================================


async def get_request_id(
    x_request_id: str | None = Header(None, alias="X-Request-ID"),
) -> str | None:
    """
    Extract request ID from headers for tracing.

    Args:
        x_request_id: Request ID from X-Request-ID header

    Returns:
        Request ID if provided, None otherwise
    """
    return x_request_id


RequestID = Annotated[str | None, Depends(get_request_id)]


# =============================================================================
# Rate Limiting Metadata
# =============================================================================


async def get_client_info(
    x_real_ip: str | None = Header(None, alias="X-Real-IP"),
    x_forwarded_for: str | None = Header(None, alias="X-Forwarded-For"),
) -> Dict[str, Any]:
    """
    Extract client information from headers (set by Nginx).

    Args:
        x_real_ip: Real client IP from Nginx
        x_forwarded_for: Forwarded-for chain

    Returns:
        Dictionary with client information
    """
    client_ip = x_real_ip
    if not client_ip and x_forwarded_for:
        # Take the first IP in the chain
        client_ip = x_forwarded_for.split(",")[0].strip()

    return {
        "client_ip": client_ip,
        "forwarded_for": x_forwarded_for,
    }


ClientInfo = Annotated[Dict[str, Any], Depends(get_client_info)]


# =============================================================================
# Service-Specific Dependencies
# =============================================================================


def require_role(required_role: UserRole):
    """
    Factory function to create a role requirement dependency.

    Args:
        required_role: The role required for access

    Returns:
        Dependency function that validates role
    """

    async def check_role(current_user: ActiveUser) -> User:
        role_hierarchy = {
            UserRole.USER: 0,
            UserRole.ADMIN: 1,
        }

        if role_hierarchy.get(current_user.role, 0) < role_hierarchy.get(
            required_role, 0
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role.value}' or higher required",
            )
        return current_user

    return check_role


# =============================================================================
# Health Check Dependencies
# =============================================================================


async def verify_service_health() -> Dict[str, str]:
    """
    Basic health check dependency.

    Returns:
        Dictionary with health status
    """
    return {"status": "healthy"}


HealthStatus = Annotated[Dict[str, str], Depends(verify_service_health)]
