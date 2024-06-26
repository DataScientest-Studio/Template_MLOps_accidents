from fastapi import FastAPI, Depends
from fastapi import HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import RedirectResponse, Response
import secrets
import uvicorn
import requests

from pydantic import BaseModel
from typing import Optional

app = FastAPI()
security = HTTPBasic()

# Hardcoded username and password for simplicity
USERNAME = "admin"
PASSWORD = "password"

streamlit_url = "http://localhost:8501"

predict_url = "http://localhost:8000/predict"

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, USERNAME)
    correct_password = secrets.compare_digest(credentials.password, PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username



# Data for prediction


class Features(BaseModel):
    place: int = 10
    catu: int = 3
    sexe: int = 1
    secu1: float =0.0
    year_acc: int = 2021
    victim_age: int = 60
    catv: int = 2
    obsm: int = 1
    motor: int = 1
    catr: int = 3
    circ: int = 2
    surf: int = 1
    situ:int =  1
    vma: int = 50
    jour: int = 7
    mois: int = 12
    lum: int = 5
    dep: int = 77
    com: int = 77317
    agg_: int = 2
    int_: int = 1
    atm: int =  0
    col: int = 6
    lat: float = 48.60
    long: float = 2.89
    hour: int = 17
    nb_victim: int = 2
    nb_vehicules: int  = 1


@app.get("/", name="Status")
def get_status():
    """Returns message if for running"""
    return {"GreenLightServices API": "Running"}


@app.get("/request_status", name="Status")
def get_status():
    """Returns message if for running"""
    return {"GreenLightServices API": "For later monitoring purposes"}


@app.get("/login", name="Login")
def login(username: str = Depends(authenticate)):
    # cmd = ["streamlit", "run", "app.py"]
    # # Run the command
    # process = subprocess.Popen(cmd)
    response = RedirectResponse(url="/streamlit")
    return f"Authentication successful. You can enter application GreenLightServices on localhost:8000/streamlit {response}"

@app.get("/streamlit", name="GreenLightServices")
async def streamlit_proxy(username: str = Depends(authenticate)):
    return RedirectResponse(url=streamlit_url)

@app.put("/prediction", name="Prediction")
async def prediction(features: Features):
    response = requests.post(url=predict_url, json=features.model_dump())
    return {"prediction": response.json}


# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)


# @app.get("/streamlit/{path:path}")
# async def streamlit_proxy(path: str, token: str = Depends(oauth2_scheme)):
#     url = f"http://localhost:8501/{path}"
#     response = requests.get(url)
#     return Response(content=response.content, status_code=response.status_code)
