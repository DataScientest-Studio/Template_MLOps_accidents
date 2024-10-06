import pytest
import requests

# Sample credentials for users
VALID_CREDENTIALS_USER1 = ("user1", "datascientest")
VALID_CREDENTIALS_ADMIN = ("admin", "adminsecret")
INVALID_CREDENTIALS = ("user1", "wrongpassword")


# Défine API GATEWAY URL
API_GATEWAY_MONITOR = "http://localhost:8000/monitor"


# Test the /monitor endpoint with admin credentials
def test_monitor_endpoint_as_admin():
    response = requests.get(
        url=API_GATEWAY_MONITOR,
        auth=VALID_CREDENTIALS_ADMIN 
    )
    
    assert response.status_code == 200
    response_json = response.json()
    assert 'accuracy' in response_json
    accuracy = response_json['accuracy'][0]
    assert accuracy > 0.6
    assert 'data_drift' in response_json
    assert 'model_drift' in response_json



# Test the /monitor endpoint without admin credentials
def test_monitor_endpoint_as_user():
    response = requests.get(
        url=API_GATEWAY_MONITOR,
        auth=VALID_CREDENTIALS_USER1 
    )
    
    assert response.status_code == 403
    

  
