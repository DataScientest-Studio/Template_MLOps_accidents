"""Dashboard configuration."""

import os

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:80").rstrip("/")
SESSION_EXPIRE_MINUTES = int(os.environ.get("SESSION_EXPIRE_MINUTES", "30"))
API_TIMEOUT = 30.0
