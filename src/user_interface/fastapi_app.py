from fastapi import FastAPI, Depends
from fastapi import HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.responses import RedirectResponse
import secrets
import subprocess

app = FastAPI()
security = HTTPBasic()

# Hardcoded username and password for simplicity
USERNAME = "admin"
PASSWORD = "password"


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


@app.get("/", name="Status")
def get_status():
    """Returns message if for running"""
    return {"GreenLightServices API": "Running"}


@app.get("/request_status", name="Status")
def get_status():
    """Returns message if for running"""
    return {"GreenLightServices API": "Running"}


@app.get("/login", name="Login")
def login(username: str = Depends(authenticate)):
    # cmd = ["streamlit", "run", "app.py"]
    # # Run the command
    # process = subprocess.Popen(cmd)
    # # RedirectResponse(url="/streamlit")
    return "Authentication successful. You can enter application on localhost:8000/streamlit."


@app.get("/streamlit", name="Streamlit")
def serve_streamlit(username: str = Depends(authenticate)):
    cmd = ["streamlit", "run", "app.py"]
    # Run the command
    process = subprocess.Popen(cmd)
    return process.returncode
