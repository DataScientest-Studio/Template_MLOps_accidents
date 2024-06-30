from fastapi import FastAPI, Depends
from fastapi import HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import RedirectResponse, Response
import secrets
import uvicorn
import requests

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


# @app.post("/token")
# async def login(username: str = Depends(authenticate)):
    
#     return {"access_token": username}

# @app.get("/")
# async def read_root(username: str = Depends(authenticate)):
#     return RedirectResponse(url="/streamlit")

# @app.get("/streamlit/{path:path}")
# async def streamlit_proxy(path: str, usernam: str = Depends(authenticate)):
#     url = f"http://localhost:8501/{path}"
#     response = requests.get(url)
#     return Response(content=response.content, status_code=response.status_code)

# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, StreamingResponse
import httpx

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello from FastAPI"}

@app.get("/streamlit/{path:path}")
async def proxy_streamlit(path: str, request: Request):
    print(path)
    url = f"http://localhost:8501/{path}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return StreamingResponse(response.aiter_raw(), status_code=response.status_code, headers=response.headers)

@app.get("/redirect_to_streamlit")
async def redirect_to_streamlit():
    return RedirectResponse(url="http://localhost:8501")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
