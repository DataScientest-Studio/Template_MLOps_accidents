"""
Common module for MLOps microservices.

Provides shared functionality across all services:
- JWT authentication and authorization
- Role-based access control (RBAC)
- Common Pydantic models
- Shared configuration
- Async job management
"""

from .auth import (
    UserRole,
    create_access_token,
    create_refresh_token,
    get_current_active_user,
    get_current_user,
    get_password_hash,
    require_admin,
    require_user,
    verify_password,
    verify_token,
)
from .config import settings
from .job_store import Job, JobStatus, JobStore, JobType, job_store
from .models import (
    Token,
    TokenData,
    User,
    UserCreate,
    UserInDB,
    UserResponse,
)

__all__ = [
    # Auth
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "get_password_hash",
    "verify_password",
    "get_current_user",
    "get_current_active_user",
    "require_admin",
    "require_user",
    "UserRole",
    # Config
    "settings",
    # Job Store
    "Job",
    "JobStatus",
    "JobType",
    "JobStore",
    "job_store",
    # Models
    "Token",
    "TokenData",
    "User",
    "UserInDB",
    "UserCreate",
    "UserResponse",
]
