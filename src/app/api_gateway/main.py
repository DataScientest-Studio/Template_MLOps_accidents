from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from passlib.context import CryptContext
from pydantic import BaseModel
import requests
import httpx
from typing import Dict

app = FastAPI(
    title="SafeRoads",
    description=" API de Prédiction de la gravité des accidents routiers en France.")

# Définir les URLs des services internes
PREDICTION_SERVICE_URL = "http://prediction_service:8001/predict"
RETRAIN_SERVICE_URL = "http://retrain_service:8003/retrain"
DB_SERVICE_URL = "http://db_service:5432/query"
MONITORING_SERVICE_URL = "http://monitoring_service:8002/monitor"


security = HTTPBasic()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

users = {
    "user1": {
        "username": "user1",
        "name": "Sousou",
        "hashed_password": pwd_context.hash('datascientest'),
        "role": "standard",
    },
    "user2": {
        "username": "user2",
        "name": "Mim",
        "hashed_password": pwd_context.hash('secret'),
        "role": "standard",
    },
    "admin": {
        "username": "admin",
        "name": "Admin",
        "hashed_password": pwd_context.hash('adminsecret'),
        "role": "admin",
    }
}

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    username = credentials.username
    user = users.get(username)
    if not user or not pwd_context.verify(credentials.password, user['hashed_password']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiant ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user

def get_current_active_user(user: dict = Depends(get_current_user)):
    if user.get("role") not in ["standard", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Utilisateur inactif",
        )
    return user

def get_current_admin_user(user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Droits non autorisés",
        )
    return user

# Définir la classe de données pour la prédiction
class DonneesAccident(BaseModel):
    num_acc : int
    place: int
    catu: int
    trajet: float
    an_nais: int
    catv: int
    choc: float
    manv: float
    mois: int
    jour: int
    lum: int
    agg: int
    int: int
    col: float
    com: int
    dep: int
    hr: int
    mn: int
    catr: int
    circ: float
    nbv: int
    prof: float
    plan: float
    lartpc: int
    larrout: int
    situ: float

# Endpoints de l'API Gateway

################################## statut de l'API Gateway ###################################

@app.get("/status", tags=["Status"])
def current_user(user: dict = Depends(get_current_active_user)):
    return {"message": f"Bienvenue sur notre API Gateway, {user['name']}!"}

################################## microservice prédiction ###################################   
@app.post("/prediction", tags=["Prediction"])
async def call_prediction_service(accident: DonneesAccident, user: dict = Depends(get_current_active_user)):
     """
    Endpoint pour prédire la gravité de l'accident en appelant le service de prédiction.

    Args:
    - accident : Les données de l'accident 
    - user : L'utilisateur récupéré à partir de la dépendance `get_current_active_user`.

    Returns:
    - response: La prédiction de la gravité de l'accident.
    """
     payload = accident.model_dump()
     response = requests.post(url=PREDICTION_SERVICE_URL, json=payload, timeout=30)
     return response.json()
################################## microservice retraining ###################################
@app.post("/retrain", tags=["Retrain"])
async def retrain(user: dict = Depends(get_current_admin_user)):
    """
    Endpoint pour réentraîner le modèle en appelant le service de réentraînement.

    Args:
    - user : L'utilisateur récupéré à partir de la dépendance `get_current_admin_user`.

    Returns:
    - dict: Confirmation de la demande de réentraînement.
    """
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(RETRAIN_SERVICE_URL)
        response.raise_for_status() 
        return response.json()

################################## microservice monitoring ###################################
@app.get("/monitor",tags=["Monitoring"])
async def monitor(user: dict = Depends(get_current_admin_user)):
    """
    Endpoint pour surveiller l'accuracy du modèle,vérifier qu'il y a pas de drift (data+model).
    
    Accessible uniquement aux admin.

    Si il ya un drift il déclenche un retraning en evoyant un request à l'api de retrain

    Args:
    - user : L'utilisateur récupéré à partir de la dépendance `get_current_admin_user`.

    Returns:
    - dict: Contient l'accuracy actuelle du modèle et la présence du drift ou non.
    """

    async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.get(MONITORING_SERVICE_URL)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                raise HTTPException(status_code=500, detail=f"Monitoring service error: {exc.response.text}")
