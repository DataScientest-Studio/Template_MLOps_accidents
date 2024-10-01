import pytest
import requests


# Sample credentials for users
VALID_CREDENTIALS_USER1 = ("user1", "datascientest")
VALID_CREDENTIALS_ADMIN = ("admin", "adminsecret")
INVALID_CREDENTIALS = ("user1", "wrongpassword")

# Défine API GATEWAY URL 
API_GATEWAY_RETRAIN = "http://localhost:8000/retrain"

# Test the /retrain endpoint with admin credentials
def test_retrain_endpoint_as_admin():
    response = requests.post(
        url=API_GATEWAY_RETRAIN ,
        auth=VALID_CREDENTIALS_ADMIN
    )
    
    assert response.status_code == 200
    assert response.json() == {"message": "Re-entrainement réussi"}


# Test the /retrain endpoint without admin credentials
def test_retrain_endpoint_as_user():
    response = requests.post(
        url=API_GATEWAY_RETRAIN ,
        auth=VALID_CREDENTIALS_USER1  
    )
    
    assert response.status_code == 403
    
