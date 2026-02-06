# Microservices Architecture Implementation Plan

## Architecture Overview

Transform the monolithic MLOps project into 4 microservices:

1. **Auth Service**: Handles authentication and user management (JWT tokens, user CRUD)
2. **Data Service**: Handles data preprocessing (`make_dataset.py`, `build_features.py`)
3. **Train Service**: Handles model training (`train_multi_model.py`, `base_trainer.py`)
4. **Predict Service**: Handles model inference (`predict_model.py`)

All services will be containerized with individual Dockerfiles, orchestrated via docker-compose, and fronted by Nginx as a reverse proxy with JWT authentication.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Docker Network                                  │
│                                                                             │
│    ┌──────────┐                                                             │
│    │  Client  │                                                             │
│    └────┬─────┘                                                             │
│         │                                                                   │
│         ▼                                                                   │
│    ┌──────────┐    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│    │  Nginx   │───▶│ Auth :8004  │  │ Data :8001  │  │ Train :8002 │  │Predict :8003│  │
│    │  (JWT)   │───▶│             │  │             │  │             │  │             │  │
│    │   :80    │───▶│ User Store  │  │  Job Store  │  │  Job Store  │  │             │  │
│    └──────────┘    └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────────────┘  │
│                                │                │                          │
│                         ┌──────┴────────────────┴──────┐                   │
│                         │      Shared Volumes          │                   │
│                         │   /data    /models   /src    │                   │
│                         └──────────────────────────────┘                   │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       │ HTTPS
                                       ▼
                         ┌─────────────────────────────┐
                         │   External Infrastructure   │
                         │  ┌───────────────────────┐  │
                         │  │  DagsHub MLflow       │  │
                         │  │  (Remote Tracking)    │  │
                         │  └───────────────────────┘  │
                         │  ┌───────────────────────┐  │
                         │  │  DagsHub DVC Remote   │  │
                         │  │  (Data Storage)       │  │
                         │  └───────────────────────┘  │
                         └─────────────────────────────┘
```

## Async Job Pattern

Long-running operations (preprocessing, training) use an async job pattern to avoid HTTP timeouts:

```
┌────────┐                    ┌─────────┐                    ┌─────────────┐
│ Client │                    │  Nginx  │                    │   Service   │
└───┬────┘                    └────┬────┘                    └──────┬──────┘
    │                              │                                │
    │── POST /train ──────────────▶│                                │
    │                              │───────────────────────────────▶│
    │                              │                                │ create job
    │◀── 202 Accepted ────────────│◀── {job_id: "abc123"} ────────│ start background
    │    {job_id: "abc123"}        │                                │
    │                              │                    ┌───────────┴───────────┐
    │                              │                    │   Background Worker   │
    │                              │                    │   (actual training)   │
    │                              │                    └───────────┬───────────┘
    │                              │                                │
    │── GET /status/abc123 ───────▶│                                │
    │                              │───────────────────────────────▶│
    │◀── {status: "running"} ─────│◀───────────────────────────────│
    │                              │                                │
    │     ... poll again ...       │                                │
    │                              │                                │
    │── GET /status/abc123 ───────▶│                                │
    │◀── {status: "completed"} ───│◀───────────────────────────────│
```

**Benefits:**
- No HTTP timeout issues (requests return immediately)
- Progress tracking via polling
- Job history and status persistence
- Can be upgraded to WebSocket for real-time updates

## Implementation Structure

### 1. Project Structure

```
services/
├── common/                    # Shared code across services
│   ├── __init__.py
│   ├── auth.py               # JWT authentication & RBAC
│   ├── config.py             # Shared configuration (Pydantic Settings)
│   ├── dependencies.py       # FastAPI dependencies
│   ├── job_store.py          # Async job management
│   └── models.py             # Common Pydantic models
│
├── auth_service/
│   ├── Dockerfile
│   ├── main.py               # FastAPI app
│   └── api/
│       ├── __init__.py
│       └── routes.py         # Auth endpoints (login, refresh, users)
│
├── data_service/
│   ├── Dockerfile
│   ├── main.py               # FastAPI app
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py         # API endpoints
│   │   └── schemas.py        # Request/Response models
│   └── core/
│       ├── __init__.py
│       ├── preprocessing.py  # Wraps make_dataset.py
│       └── features.py       # Wraps build_features.py
│
├── train_service/
│   ├── Dockerfile
│   ├── main.py               # FastAPI app
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── schemas.py
│   └── core/
│       ├── __init__.py
│       └── trainer.py        # Wraps train_multi_model.py
│
├── predict_service/
│   ├── Dockerfile
│   ├── main.py               # FastAPI app
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── schemas.py
│   └── core/
│       ├── __init__.py
│       └── predictor.py      # Wraps predict_model.py
│
├── nginx/
│   ├── nginx.conf            # Nginx configuration
│   └── Dockerfile            # Custom Nginx image
│
└── env.example               # Environment variables template
```

### 2. Common Security Module (`services/common/auth.py`)

- JWT token generation/validation using `python-jose[cryptography]`
- Password hashing with `passlib[bcrypt]`
- Role-based access control decorators/dependencies
- User management (admin/normal user)
- Token refresh mechanism

### 3. Async Job Store (`services/common/job_store.py`)

- In-memory job tracking (upgradeable to Redis/PostgreSQL)
- Job lifecycle: PENDING → RUNNING → COMPLETED/FAILED
- Progress tracking (0-100%)
- Job history with FIFO eviction
- Thread-safe with asyncio locks

### 4. Individual Dockerfiles

Each service gets its own Dockerfile:

- Base image: `python:3.11-slim`
- Install dependencies from `requirements.txt`
- Copy service-specific code + common module
- Expose service port (8001, 8002, 8003)
- Health check endpoints

### 5. Docker Compose Configuration

- 5 service containers (nginx, auth, data, train, predict)
- Remote MLflow on DagsHub (no local MLflow container)
- Shared volumes for `data/` and `models/`
- Environment variables from `.env` file (including DagsHub credentials)
- Network configuration for service communication

### 6. Nginx Configuration

- Reverse proxy rules for each service
- JWT validation forwarded to services
- Rate limiting (different zones for auth, general, predict)
- CORS configuration
- Health check endpoints

## API Endpoints Design

### Auth Service (`/api/v1/auth/`)

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/login` | POST | Public | Get access token |
| `/refresh` | POST | Public | Refresh access token |
| `/me` | GET | User | Get current user info |
| `/users` | GET | Admin | List all users |
| `/users` | POST | Admin | Create new user |
| `/health` | GET | Public | Health check |

### Data Service (`/api/v1/data/`)

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/preprocess` | POST | Admin | Trigger preprocessing (returns job_id) |
| `/build-features` | POST | Admin | Trigger feature engineering (returns job_id) |
| `/status/{job_id}` | GET | Admin | Check job status |
| `/jobs` | GET | Admin | List all jobs |
| `/health` | GET | Public | Health check |

### Train Service (`/api/v1/train/`)

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/` | POST | Admin | Trigger model training (returns job_id) |
| `/status/{job_id}` | GET | Admin | Check training status |
| `/jobs` | GET | Admin | List training jobs |
| `/fetch-best-model` | POST | Admin | Fetch best model from MLflow |
| `/models` | GET | Admin | List available models (MLflow) |
| `/metrics/{model_type}` | GET | Admin | Get model metrics |
| `/health` | GET | Public | Health check |

### Predict Service (`/api/v1/predict/`)

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/` | POST | User | Make single prediction |
| `/batch` | POST | User | Make batch predictions |
| `/models` | GET | User | List available models |
| `/health` | GET | Public | Health check |

## Security Implementation

### JWT Token Structure

```json
{
  "sub": "username",
  "role": "admin|user",
  "exp": 1234567890,
  "type": "access|refresh"
}
```

### Role-Based Access Control

| Role | Data Service | Train Service | Predict Service |
|------|--------------|---------------|-----------------|
| Admin | Full access | Full access | Full access |
| User | No access | No access | Predict only |

### FastAPI Dependencies

```python
from services.common.dependencies import AdminUser, AuthenticatedUser

# Admin-only endpoint
@router.post("/train")
async def train(user: AdminUser):
    ...

# Any authenticated user
@router.post("/predict")
async def predict(user: AuthenticatedUser):
    ...
```

## Shared Storage Strategy

- **Development**: Docker volumes for `data/` and `models/`
- **Production** (optional): S3/DVC remote for data, MLflow for models
- Services read/write to shared locations
- DVC integration maintained in data and train services

## Key Files

### Created Files

| File | Description |
|------|-------------|
| `services/common/auth.py` | JWT authentication utilities |
| `services/common/config.py` | Pydantic settings |
| `services/common/dependencies.py` | FastAPI dependencies |
| `services/common/job_store.py` | Async job management |
| `services/common/models.py` | Pydantic models |
| `services/auth_service/` | Dedicated authentication service |
| `services/nginx/nginx.conf` | Nginx configuration |
| `services/nginx/Dockerfile` | Nginx image |
| `services/*/Dockerfile` | Service Dockerfiles |
| `services/env.example` | Environment template |
| `docker-compose.yml` | Orchestration (merged) |

### Modified Files

| File | Change |
|------|--------|
| `requirements.txt` | Added FastAPI dependencies |
| `pyproject.toml` | Added FastAPI dependencies |

## Dependencies

```
# FastAPI & ASGI
fastapi>=0.109.0
uvicorn[standard]>=0.27.0

# Authentication
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6

# Configuration
pydantic>=2.5.0
pydantic-settings>=2.1.0

# HTTP client
httpx>=0.26.0

# Utilities
python-dotenv>=1.0.0
```

## Migration Strategy

1. ✅ Create common auth module
2. ✅ Create job store for async operations
3. ✅ Set up Nginx reverse proxy
4. ✅ Create dedicated auth service
5. ⬜ Create data service (FastAPI app)
6. ⬜ Create train service (FastAPI app)
7. ⬜ Create predict service (FastAPI app)
8. ⬜ Integrate JWT authentication
9. ⬜ Test end-to-end workflow
10. ⬜ Update documentation

## Environment Variables

```bash
# JWT Configuration
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Admin User
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change-me
ADMIN_EMAIL=admin@mlops.local

# Service Configuration
DEBUG=false
LOG_LEVEL=INFO

# MLflow (DagsHub Remote)
# Get credentials from: https://dagshub.com/user/settings/tokens
MLFLOW_TRACKING_URI=https://dagshub.com/<username>/<repo>.mlflow
MLFLOW_TRACKING_USERNAME=your-dagshub-username
MLFLOW_TRACKING_PASSWORD=your-dagshub-token
```

## Production Considerations

### Job Store Upgrade Path

| Option | Use Case |
|--------|----------|
| In-memory (current) | Development, single instance |
| Redis | Production, multiple instances, real-time updates |
| PostgreSQL | Full persistence, queryable history |
| Celery + Redis | Complex workflows, retries, scheduling |

### Scaling

- Auth service can scale independently (stateless, validates tokens)
- Nginx can load balance multiple instances of predict service
- Data and train services typically run single instance (write operations)
- Consider Kubernetes for production scaling

### Monitoring

- Health endpoints for all services
- MLflow for model metrics and experiment tracking
- Consider adding Prometheus metrics endpoints
