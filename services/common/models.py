"""
Common Pydantic models for MLOps microservices.

Provides shared data models for:
- User management
- Authentication tokens
- API responses
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

# =============================================================================
# Enums
# =============================================================================


class UserRole(str, Enum):
    """User roles for RBAC."""

    ADMIN = "admin"
    USER = "user"


class JobStatus(str, Enum):
    """Status for async jobs (training, preprocessing)."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# =============================================================================
# Authentication Models
# =============================================================================


class Token(BaseModel):
    """OAuth2 token response model."""

    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int = Field(description="Token expiration time in seconds")


class TokenData(BaseModel):
    """Data extracted from JWT token."""

    username: Optional[str] = None
    role: Optional[UserRole] = None
    exp: Optional[datetime] = None


class TokenRefreshRequest(BaseModel):
    """Request model for token refresh."""

    refresh_token: str


class LoginRequest(BaseModel):
    """Request payload for login. Username aligned with UserBase (3–50 chars)."""

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=1, max_length=1024)

    @field_validator("username")
    @classmethod
    def username_no_whitespace_or_control(cls, v: str) -> str:
        """Reject leading/trailing whitespace and control characters."""
        if v != v.strip():
            raise ValueError("Username must not have leading or trailing whitespace")
        if any(ord(c) < 32 and c not in "\t\n\r" for c in v) or any(
            ord(c) == 127 for c in v
        ):
            raise ValueError("Username must not contain control characters")
        return v


class LoginResponse(BaseModel):
    """Response payload for login."""

    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int


class ForgotPasswordRequest(BaseModel):
    """Request payload for forgot password (request reset token)."""

    username: str = Field(..., min_length=3, max_length=50)


class ForgotPasswordResponse(BaseModel):
    """Response for forgot password. In dev, reset_token may be returned."""

    message: str = "If an account exists, a reset link has been sent."
    reset_token: Optional[str] = None  # Only in dev / when email not configured


class ResetPasswordRequest(BaseModel):
    """Request payload for resetting password with token."""

    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=1024)


# =============================================================================
# User Models
# =============================================================================


class UserBase(BaseModel):
    """Base user model with common fields."""

    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER


class UserCreate(UserBase):
    """Model for creating a new user."""

    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """Model for updating user information."""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None


class User(UserBase):
    """User model returned by API."""

    id: int
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserInDB(User):
    """User model with hashed password (internal use only)."""

    hashed_password: str


class UserResponse(BaseModel):
    """Simplified user response (without sensitive fields)."""

    id: int
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: UserRole
    is_active: bool


# =============================================================================
# API Response Models
# =============================================================================


class APIResponse(BaseModel):
    """Standard API response wrapper."""

    success: bool
    message: str
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = "healthy"
    service: str
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# Job Models (for async operations)
# =============================================================================


class JobCreate(BaseModel):
    """Model for creating a new job."""

    job_type: str
    parameters: Optional[Dict[str, Any]] = None


class JobResponse(BaseModel):
    """Response model for job status."""

    job_id: str
    status: JobStatus
    job_type: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress: Optional[float] = Field(None, ge=0, le=100)
    message: Optional[str] = None
    logs: Optional[List[str]] = None


class JobsListResponse(BaseModel):
    """Paginated list of jobs with total count."""

    items: List[JobResponse]
    total: int


# =============================================================================
# Model/Training Related Models
# =============================================================================


class ModelInfo(BaseModel):
    """Information about a trained model."""

    model_name: str
    model_type: str
    version: str
    created_at: datetime
    metrics: Optional[Dict[str, float]] = None
    parameters: Optional[Dict[str, Any]] = None
    is_active: bool = False


class ModelMetrics(BaseModel):
    """Model performance metrics."""

    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    roc_auc: Optional[float] = None
    additional_metrics: Optional[Dict[str, float]] = None


class TrainingRequest(BaseModel):
    """Request model for training."""

    model_types: List[str] = Field(
        default=["logistic_regression"],
        description="List of model types to train",
    )
    hyperparameters: Optional[Dict[str, Dict[str, Any]]] = None
    experiment_name: Optional[str] = None


class TrainingResponse(BaseModel):
    """Response model for training request."""

    job_id: str
    status: JobStatus
    model_types: List[str]
    message: str


# =============================================================================
# Prediction Models
# =============================================================================


class PredictionRequest(BaseModel):
    """Request model for predictions."""

    features: Dict[str, Any]
    model_name: Optional[str] = None


class PredictionResponse(BaseModel):
    """Response model for predictions."""

    prediction: Any
    probability: Optional[Dict[str, float]] = None
    model_name: str
    model_version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BatchPredictionRequest(BaseModel):
    """Request model for batch predictions."""

    features_list: List[Dict[str, Any]]
    model_name: Optional[str] = None


class BatchPredictionResponse(BaseModel):
    """Response model for batch predictions."""

    predictions: List[Any]
    probabilities: Optional[List[Dict[str, float]]] = None
    model_name: str
    model_version: str
    count: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
