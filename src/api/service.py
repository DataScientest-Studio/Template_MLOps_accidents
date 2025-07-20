import bentoml
from bentoml.io import JSON
import joblib
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Depends, HTTPException, Request
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

# --- Auth/Config ---
load_dotenv()
SECRET_KEY = os.getenv("JWT_SECRET", "I_know_that_this _is_unsecure_but_I_don't_care")
ALGORITHM = "HS256"
USERNAME = "admin"
PASSWORD = "4dm1N"

# --- Load columns (order) for prediction ---
COLUMNS_PATH = "trained_model_columns.npy"
if os.path.exists(COLUMNS_PATH):
    TRAIN_COLS = np.load(COLUMNS_PATH, allow_pickle=True)
else:
    TRAIN_COLS = None

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

class HTTPBearer401(HTTPBearer):
    async def __call__(self, request: Request):
        try:
            return await super().__call__(request)
        except HTTPException as exc:
            if exc.status_code == 403:
                raise HTTPException(status_code=401, detail="Not authenticated")
            raise

def load_model():
    try:
        if os.path.exists("trained_model.joblib"):
            return joblib.load("trained_model.joblib")
        else:
            raise FileNotFoundError("trained_model.joblib nicht gefunden!")
    except Exception as e:
        print(f"Fehler beim Laden des Modells: {e}")
        return None

# --- Airflow Webhook Classes and Schemas ---
logger = logging.getLogger(__name__)

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

class AirflowAPIClient:
    """Simple Airflow API client for triggering DAGs and checking status"""
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.auth = HTTPBasicAuth(username, password)
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def trigger_dag(self, dag_id: str, config: dict = None) -> dict:
        url = f"{self.base_url}/api/v2/dags/{dag_id}/dagRuns"
        payload = {
            "dag_run_id": f"manual__{int(time.time())}",
            "conf": config or {}
        }
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    def get_dag_run_status(self, dag_id: str, dag_run_id: str) -> dict:
        url = f"{self.base_url}/api/v2/dags/{dag_id}/dagRuns/{dag_run_id}"
        response = self.session.get(url)
        response.raise_for_status()
        data = response.json()
        return {
            "state": data.get("state"),
            "start_date": data.get("start_date"),
            "end_date": data.get("end_date"),
            "execution_date": data.get("execution_date")
        }

    def get_dag_runs(self, dag_id: str, limit: int = 10) -> list:
        url = f"{self.base_url}/api/v2/dags/{dag_id}/dagRuns"
        params = {"limit": limit, "order_by": "-execution_date"}
        response = self.session.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("dag_runs", [])

def setup_airflow_client():
    airflow_base_url = os.getenv("AIRFLOW_BASE_URL", "http://airflow-apiserver:8080")
    airflow_username = os.getenv("AIRFLOW_USERNAME", "airflow")
    airflow_password = os.getenv("AIRFLOW_PASSWORD", "airflow")
    try:
        return AirflowAPIClient(airflow_base_url, airflow_username, airflow_password)
    except Exception as e:
        logger.error(f"Could not connect to Airflow: {e}")
        return None

model = load_model()
airflow_client = setup_airflow_client()
svc = bentoml.Service("accident_prediction_with_webhook")

def create_jwt_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer401())):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def admission_request_to_dataframe(admission_request: AdmissionRequest) -> pd.DataFrame:
    data = pd.DataFrame([admission_request.dict()])
    data = pd.get_dummies(data)
    if TRAIN_COLS is not None:
        data = data.reindex(columns=TRAIN_COLS, fill_value=0)
    return data

app = FastAPI(title="Admission Prediction API with Webhook", version="1.0.0")

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
    input_df = admission_request_to_dataframe(input_data)
    prediction = model.predict(input_df)
    score = round(float(prediction[0]), 3)
    predict_with_auth.prediction_score_gauge.set(score)
    return {
        "chance_of_admit": score,
        "processing_time": round(time.time() - prediction_start, 3)
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
    input_df = admission_request_to_dataframe(input_data)
    prediction = model.predict(input_df)
    score = round(float(prediction[0]), 3)
    return {
        "chance_of_admit": score,
        "processing_time": round(time.time() - prediction_start, 3)
    }

@app.post("/trigger-ml-pipeline", response_model=PipelineResponse, dependencies=[Depends(verify_token)])
async def trigger_ml_pipeline(request: TriggerPipelineRequest):
    try:
        if airflow_client is None:
            raise HTTPException(status_code=500, detail="Airflow client not initialized")
        config = {
            "model_type": request.model_type,
            "retrain_from_scratch": request.retrain,
            "triggered_by": "bentoml_webhook",
            "timestamp": datetime.now().isoformat()
        }
        result = airflow_client.trigger_dag("ml_pipeline_with_mlflow", config=config)
        return PipelineResponse(
            success=True,
            dag_run_id=result.get("dag_run_id"),
            message="ML Pipeline triggered successfully",
            config=config
        )
    except Exception as e:
        logger.error(f"Error triggering ML pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pipeline-status/{dag_run_id}", response_model=StatusResponse)
async def get_pipeline_status(dag_run_id: str):
    try:
        if airflow_client is None:
            raise HTTPException(status_code=500, detail="Airflow client not initialized")
        status = airflow_client.get_dag_run_status("ml_pipeline_with_mlflow", dag_run_id)
        return StatusResponse(
            success=True,
            dag_run_id=dag_run_id,
            state=status["state"],
            start_date=status["start_date"],
            end_date=status.get("end_date")
        )
    except Exception as e:
        logger.error(f"Error getting pipeline status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Mount FastAPI app to BentoML service
svc.mount_asgi_app(app)

