"""
Shared configuration for MLOps microservices.

Configuration is loaded from environment variables with sensible defaults.
"""

from functools import lru_cache
from typing import List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ==========================================================================
    # JWT Configuration
    # ==========================================================================
    JWT_SECRET_KEY: str = ""  # Required: set in .env (e.g. openssl rand -hex 32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 600  # 10 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ==========================================================================
    # Service Configuration
    # ==========================================================================
    SERVICE_NAME: str = "mlops-service"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # ==========================================================================
    # Service URLs (for inter-service communication)
    # ==========================================================================
    DATA_SERVICE_URL: str = "http://data:8001"
    TRAIN_SERVICE_URL: str = "http://train:8002"
    PREDICT_SERVICE_URL: str = "http://predict:8003"

    # ==========================================================================
    # MLflow Configuration (DagsHub Remote)
    # ==========================================================================
    MLFLOW_TRACKING_URI: str = ""  # Set via environment variable
    MLFLOW_TRACKING_USERNAME: str = ""  # DagsHub username
    MLFLOW_TRACKING_PASSWORD: str = ""  # DagsHub token
    MLFLOW_EXPERIMENT_NAME: str = "accident_severity"

    # ==========================================================================
    # Data Paths
    # ==========================================================================
    DATA_DIR: str = "/app/data"
    MODELS_DIR: str = "/app/models"
    RAW_DATA_DIR: str = "/app/data/raw"
    PREPROCESSED_DATA_DIR: str = "/app/data/preprocessed"

    # ==========================================================================
    # Model config (train service: path to model_config.yaml; writable in Docker
    # when set to e.g. /app/data/model_config.yaml)
    # ==========================================================================
    MODEL_CONFIG_PATH: str = "src/config/model_config.yaml"

    # ==========================================================================
    # CORS Configuration
    # ==========================================================================
    # Use Union to allow both string and list, preventing pydantic-settings from
    # trying to parse as JSON before the validator runs.
    # The validator converts it to List[str] before validation.
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000,http://localhost:8080"
    
    # After validation, this will always be List[str] for use in CORSMiddleware

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v) -> List[str]:
        """
        Parse CORS origins from comma-separated string or list.
        
        Handles:
        - Comma-separated strings: "http://localhost:3000,http://localhost:8080"
        - Wildcard: "*"
        - Empty strings: defaults to wildcard
        - Already parsed lists: returns as-is
        
        Returns:
            List[str]: Always returns a list of strings
        """
        # Handle None or empty string
        if v is None or (isinstance(v, str) and not v.strip()):
            return ["*"]
        
        # Handle string input (comma-separated or wildcard)
        if isinstance(v, str):
            v = v.strip()
            # Handle wildcard
            if v == "*":
                return ["*"]
            # Handle comma-separated list
            if "," in v:
                origins = [origin.strip() for origin in v.split(",") if origin.strip()]
                return origins if origins else ["*"]
            # Single value
            return [v] if v else ["*"]
        
        # Already a list
        if isinstance(v, list):
            return v
        
        # Fallback
        return ["*"]

    # ==========================================================================
    # Database Configuration (for user storage - SQLite by default)
    # ==========================================================================
    DATABASE_URL: str = "sqlite:///./users.db"

    # ==========================================================================
    # Initial Admin User
    # ==========================================================================
    ADMIN_USERNAME: str = ""  # Required: set in .env
    ADMIN_PASSWORD: str = ""  # Required: set in .env
    ADMIN_EMAIL: str = ""  # Required: set in .env

    # ==========================================================================
    # Auth rate limits (per-username, in-memory; multi-instance needs Redis)
    # ==========================================================================
    LOGIN_RATE_LIMIT_PER_USER: int = 5
    LOGIN_RATE_WINDOW_SECONDS: int = 900  # 15 minutes
    REFRESH_RATE_LIMIT_PER_USER: int = 20
    REFRESH_RATE_WINDOW_SECONDS: int = 60

    # ==========================================================================
    # Failed login lockout
    # ==========================================================================
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 15

    # ==========================================================================
    # Password reset (dev: return token in response when no email configured)
    # ==========================================================================
    DEV_PASSWORD_RESET_TOKEN_IN_RESPONSE: bool = False

    class Config:
        """Pydantic settings configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()


# Global settings instance
settings = get_settings()
