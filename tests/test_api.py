from fastapi.testclient import TestClient
from src.api import app 

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
