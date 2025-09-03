import bentoml
from bentoml.io import JSON
import joblib
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import os
from dotenv import load_dotenv
import numpy as np
import pandas as pd
import time
import logging
import requests
from requests.auth import HTTPBasicAuth
from typing import Dict, Any, Optional

# Prometheus imports
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from fastapi.responses import Response

# Load secret key from .env or hardcode for local testing
load_dotenv()
SECRET_KEY = os.getenv("JWT_SECRET", "I_know_that_this _is_unsecure_but_I_don't_care")
ALGORITHM = "HS256"
USERNAME = "admin"
PASSWORD = "4dm1N"

# Logger setup
logger = logging.getLogger(__name__)

# --- Load columns (order) for prediction ---
COLUMNS_PATH = "trained_model_columns.npy"
if os.path.exists(COLUMNS_PATH):
    TRAIN_COLS = np.load(COLUMNS_PATH, allow_pickle=True)
else:
    TRAIN_COLS = None

# Prometheus metrics
request_count = Counter(
    "api_requests_total", "Total API requests", ["method", "endpoint", "status"]
)
request_duration = Histogram(
    "api_request_duration_seconds", "Request duration", ["method", "endpoint"]
)
prediction_count = Counter("predictions_total", "Total predictions made")
prediction_score_gauge = Gauge("last_prediction_score", "Last prediction score")
active_connections = Gauge("active_connections", "Currently active connections")
model_load_time = Gauge("model_load_time_seconds", "Time taken to load model")

# Webhook specific metrics
webhook_trigger_count = Counter(
    "webhook_triggers_total", "Total webhook triggers", ["trigger_type"]
)
pipeline_runs = Gauge("active_pipeline_runs", "Currently active pipeline runs")


# Request schemas
class AdmissionRequest(BaseModel):
    place: int
    catu: int
    sexe: int
    secu1: float
    year_acc: int
    victim_age: int
    catv: int
    obsm: int
    motor: int
    catr: int
    circ: int
    surf: int
    situ: int
    vma: int
    jour: int
    mois: int
    lum: int
    dep: int
    com: int
    agg_: int
    int: int
    atm: int
    col: int
    lat: float
    long: float
    hour: int
    nb_victim: int
    nb_vehicules: int


# Webhook Request/Response schemas
class TriggerPipelineRequest(BaseModel):
    model_type: str = "random_forest"
    retrain: bool = False


class PipelineStatusRequest(BaseModel):
    dag_run_id: str


class PipelineResponse(BaseModel):
    success: bool
    dag_run_id: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class StatusResponse(BaseModel):
    success: bool
    dag_run_id: Optional[str] = None
    state: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    error: Optional[str] = None


class HTTPBearer401(HTTPBearer):
    async def __call__(self, request: Request):
        try:
            return await super().__call__(request)
        except HTTPException as exc:
            if exc.status_code == 403:
                raise HTTPException(status_code=401, detail="Not authenticated")
            raise


def load_model():
    """Lädt das Modell direkt ohne Runner"""
    try:
        # Versuche joblib-Datei zu laden
        if os.path.exists("trained_model.joblib"):
            return joblib.load("trained_model.joblib")
        else:
            raise FileNotFoundError("trained_model.joblib nicht gefunden!")
    except Exception as e:
        print(f"Fehler beim Laden des Modells: {e}")
        return None


import requests
from requests.auth import HTTPBasicAuth
import json


class AirflowAPIClient:
    """Simple Airflow API client for triggering DAGs and checking status"""

    def __init__(
        self,
        base_url: str,
        username: str = None,
        password: str = None,
        token: str = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {"Content-Type": "application/json", "Accept": "application/json"}
        )

        if token:
            # JWT Bearer Token Auth
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        elif username and password:
            # HTTP Basic Auth
            self.session.auth = HTTPBasicAuth(username, password)
        else:
            raise ValueError("Either token or username/password must be provided.")

    def trigger_dag(self, dag_id: str, config: dict = None) -> dict:
        url = f"{self.base_url}/api/v2/dags/{dag_id}/dagRuns"
        now = datetime.now(timezone.utc).isoformat(timespec="milliseconds")

        payload = {
            "dag_run_id": f"manual__{int(time.time())}",
            "data_interval_start": now,
            "data_interval_end": now,
            "logical_date": now,
            "run_after": now,
            "conf": config or {},
            "note": "Triggered via API",
        }

        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to trigger DAG {dag_id}: {e}")
            raise Exception(f"Failed to trigger DAG: {str(e)}")

    def get_dag_run_status(self, dag_id: str, dag_run_id: str) -> dict:
        url = f"{self.base_url}/api/v2/dags/{dag_id}/dagRuns/{dag_run_id}"

        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()

            return {
                "state": data.get("state"),
                "start_date": data.get("start_date"),
                "end_date": data.get("end_date"),
                "execution_date": data.get("execution_date"),
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get DAG run status: {e}")
            raise Exception(f"Failed to get DAG run status: {str(e)}")

    def get_dag_runs(self, dag_id: str, limit: int = 10) -> list:
        url = f"{self.base_url}/api/v2/dags/{dag_id}/dagRuns"
        params = {"limit": limit, "order_by": "-execution_date"}

        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("dag_runs", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get DAG runs: {e}")
            raise Exception(f"Failed to get DAG runs: {str(e)}")


def setup_airflow_client():
    """Setup Airflow client connection"""
    # Load settings
    airflow_base_url = os.getenv("AIRFLOW_BASE_URL", "http://airflow-apiserver:8080")
    airflow_username = os.getenv("AIRFLOW_USERNAME", "airflow")
    airflow_password = os.getenv("AIRFLOW_PASSWORD", "airflow")

    logging.basicConfig(level=logging.INFO)
    # Request token
    token_url = f"{airflow_base_url}/auth/token"
    logger.info("Requesting Airflow token...")

    token_resp = requests.post(
        token_url,
        json={"username": airflow_username, "password": airflow_password},
        headers={"Content-Type": "application/json"},
    )

    if token_resp.status_code != 201:
        logger.error(
            f"Token request failed: {token_resp.status_code} {token_resp.text}"
        )
        return

    token = token_resp.json().get("access_token")
    if not token:
        logger.error("No access_token found in token response")
        return

    # Set up client with token
    client = AirflowAPIClient(base_url=airflow_base_url, token=token)
    return client


# Load model and setup clients
model = load_model()
airflow_client = setup_airflow_client()
svc = bentoml.Service("accident_prediction_with_webhook")


# Auth token generator
def create_jwt_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.now(datetime.timezone.utc) + timedelta(minutes=30),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# Token validation dependency
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer401())):
    try:
        payload = jwt.decode(
            credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM]
        )
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def admission_request_to_numpy(admission_request: AdmissionRequest) -> np.ndarray:
    features = [
        admission_request.place,
        admission_request.catu,
        admission_request.sexe,
        admission_request.secu1,
        admission_request.year_acc,
        admission_request.victim_age,
        admission_request.catv,
        admission_request.obsm,
        admission_request.motor,
        admission_request.catr,
        admission_request.circ,
        admission_request.surf,
        admission_request.situ,
        admission_request.vma,
        admission_request.jour,
        admission_request.mois,
        admission_request.lum,
        admission_request.dep,
        admission_request.com,
        admission_request.agg_,
        admission_request.int,
        admission_request.atm,
        admission_request.col,
        admission_request.lat,
        admission_request.long,
        admission_request.hour,
        admission_request.nb_victim,
        admission_request.nb_vehicules,
    ]
    return np.array([features], dtype=np.float32)


# FastAPI App with middleware for monitoring
app = FastAPI(title="Admission Prediction API with Webhook", version="1.0.0")


@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    # Increment active connections
    active_connections.inc()

    start_time = time.time()
    method = request.method
    path = request.url.path

    try:
        response = await call_next(request)
        status_code = response.status_code

        # Record metrics
        request_count.labels(method=method, endpoint=path, status=status_code).inc()
        request_duration.labels(method=method, endpoint=path).observe(
            time.time() - start_time
        )

        return response
    except Exception as e:
        # Record failed requests
        request_count.labels(method=method, endpoint=path, status="500").inc()
        request_duration.labels(method=method, endpoint=path).observe(
            time.time() - start_time
        )
        raise e
    finally:
        # Decrement active connections
        active_connections.dec()


@app.get("/metrics")
def get_metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/login")
def login(request: dict):
    username = request.get("username")
    password = request.get("password")
    if username == USERNAME and password == PASSWORD:
        token = create_jwt_token(username)
        return {"token": token}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@app.post("/predict", dependencies=[Depends(verify_token)])
async def predict_with_auth(input_data: AdmissionRequest):
    from prometheus_client import Counter, Gauge
    if not hasattr(predict_with_auth, "prediction_count"):
        predict_with_auth.prediction_count = Counter(
            'custom_predictions_total', 'Total predictions made by /predict endpoint'
        )
    if not hasattr(predict_with_auth, "prediction_score_gauge"):
        predict_with_auth.prediction_score_gauge = Gauge(
            'custom_last_prediction_score', 'Last prediction score by /predict endpoint'
        )
    predict_with_auth.prediction_count.inc()
    prediction_start = time.time()

    input_array = admission_request_to_numpy(input_data)
    prediction = model.predict(input_array)

    # Update prediction metrics
    prediction_count.inc()
    score = round(float(prediction[0]), 3)
    prediction_score_gauge.set(score)

    return {
        "chance_of_admit": score,
        "processing_time": round(time.time() - prediction_start, 3),
    }


@app.post("/predict-simple")
async def predict_simple(input_data: AdmissionRequest):
    from prometheus_client import Counter
    if not hasattr(predict_simple, "prediction_simple_count"):
        predict_simple.prediction_simple_count = Counter(
            'custom_predictions_simple_total', 'Total predictions made by /predict-simple endpoint'
        )
    predict_simple.prediction_simple_count.inc()
    prediction_start = time.time()

    input_array = admission_request_to_numpy(input_data)
    prediction = model.predict(input_array)

    # Update prediction metrics
    prediction_count.inc()
    score = round(float(prediction[0]), 3)
    prediction_score_gauge.set(score)

    return {
        "chance_of_admit": score,
        "processing_time": round(time.time() - prediction_start, 3),
    }


@app.get("/stats")
def get_stats():
    return {
        "model_load_time": model_load_time._value._value,
        "total_predictions": prediction_count._value._value,
        "last_prediction_score": prediction_score_gauge._value._value,
        "active_connections": active_connections._value._value,
        "webhook_triggers": webhook_trigger_count._value._value,
        "active_pipeline_runs": pipeline_runs._value._value,
    }


@app.post(
    "/train_model",
    response_model=PipelineResponse,
    dependencies=[Depends(verify_token)],
)
async def train_model(request: TriggerPipelineRequest):
    """
    Webhook endpoint to trigger ML pipeline (requires authentication)
    """
    try:
        if airflow_client is None:
            raise HTTPException(
                status_code=500, detail="Airflow client not initialized"
            )

        # Prepare DAG configuration
        config = {
            "model_type": request.model_type,
            "retrain_from_scratch": request.retrain,
            "triggered_by": "bentoml_webhook",
            "timestamp": datetime.now().isoformat(),
        }

        # Trigger DAG
        result = airflow_client.trigger_dag(
            "process_accidents_prediction", config=config
        )

        # Update metrics
        webhook_trigger_count.labels(trigger_type="ml_pipeline").inc()
        pipeline_runs.inc()

        return PipelineResponse(
            success=True,
            dag_run_id=result.get("dag_run_id"),
            message="ML Pipeline triggered successfully",
            config=config,
        )

    except Exception as e:
        logger.error(f"Error triggering ML pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pipeline-status/{dag_run_id}", response_model=StatusResponse)
async def get_pipeline_status(dag_run_id: str):
    try:
        if airflow_client is None:
            raise HTTPException(
                status_code=500, detail="Airflow client not initialized"
            )

        # Get DAG run status
        status = airflow_client.get_dag_run_status(
            "process_accidents_prediction", dag_run_id
        )

        # Update pipeline runs counter if completed
        if status["state"] in ["success", "failed"]:
            pipeline_runs.dec()

        return StatusResponse(
            success=True,
            dag_run_id=dag_run_id,
            state=status["state"],
            start_date=status["start_date"],
            end_date=status.get("end_date"),
        )
    except Exception as e:
        logger.error(f"Error getting pipeline status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pipeline-status", response_model=StatusResponse)
async def get_pipeline_status_post(request: PipelineStatusRequest):
    """
    Get status of a specific pipeline run (POST version)
    """
    try:
        # Validate Airflow client
        if airflow_client is None:
            raise HTTPException(
                status_code=500, detail="Airflow client not initialized"
            )

        # Get DAG run status
        status = airflow_client.get_dag_run_status(
            "process_accidents_prediction", request.dag_run_id
        )

        return StatusResponse(
            success=True,
            dag_run_id=request.dag_run_id,
            state=status["state"],
            start_date=status["start_date"],
            end_date=status.get("end_date"),
        )

    except Exception as e:
        logger.error(f"Error getting pipeline status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pipeline-runs")
async def get_recent_pipeline_runs(limit: int = 10):
    """
    Get recent pipeline runs
    """
    try:
        if airflow_client is None:
            raise HTTPException(
                status_code=500, detail="Airflow client not initialized"
            )

        runs = airflow_client.get_dag_runs("process_accidents_prediction", limit=limit)

        return {"success": True, "runs": runs, "total": len(runs)}

    except Exception as e:
        logger.error(f"Error getting pipeline runs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/airflow-status")
async def get_airflow_status():
    """
    Check Airflow connection status
    """
    try:
        if airflow_client is None:
            return {"connected": False, "type": "no_client"}

        # Try to make a simple API call to test connection
        try:
            airflow_client.session.get(
                f"{airflow_client.base_url}/api/v2/dags", timeout=5
            )
            return {
                "connected": True,
                "type": "real_client",
                "base_url": airflow_client.base_url,
            }
        except:
            return {"connected": False, "type": "connection_failed"}

    except Exception as e:
        return {"connected": False, "error": str(e)}


# Root endpoint with all available endpoints
@app.get("/")
async def root():
    return {
        "message": "Admission Prediction API with Webhook Integration",
        "version": "1.0.0",
        "endpoints": {
            "auth": {"login": "POST /login"},
            "prediction": {
                "predict_auth": "POST /predict (requires auth)",
                "predict_simple": "POST /predict-simple",
            },
            "webhook": {
                "trigger_pipeline": "POST /train_model (requires auth)",
                "trigger_pipeline_public": "POST /train_model-public",
                "get_status_get": "GET /pipeline-status/{dag_run_id}",
                "get_status_post": "POST /pipeline-status",
            },
            "monitoring": {
                "health": "GET /health",
                "metrics": "GET /metrics",
                "stats": "GET /stats",
            },
        },
    }


# Mount FastAPI app to BentoML service
svc.mount_asgi_app(app)
