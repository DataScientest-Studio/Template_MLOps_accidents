import json
import time
import requests


# Sample credentials for users
VALID_CREDENTIALS_USER1 = ("user1", "datascientest")
VALID_CREDENTIALS_ADMIN = ("admin", "adminsecret")
INVALID_CREDENTIALS = ("user1", "wrongpassword")

# Définir les URLs de API GATEWAY
API_GATEWAY_PREDICTION = "http://localhost:8000/prediction"

# Define payload
test_data = {
    "num_acc": 4000000002, #this will be remplaced with a unique identifiant 
    "place": 1,
    "catu": 2,
    "trajet": 10.0,
    "an_nais": 2024,
    "catv": 3,
    "choc": 1.0,
    "manv": 2.0,
    "mois": 6,
    "jour": 15,
    "lum": 1,
    "agg": 1,
    "int": 1,
    "col": 2.0,
    "com": 75000,
    "dep": 75,
    "hr": 14,
    "mn": 30,
    "catr": 1,
    "circ": 1.0,
    "nbv": 2,
    "prof": 0.0,
    "plan": 0.0,
    "lartpc": 0,
    "larrout": 0,
    "situ": 1.0
}

# Function to generate unique num_acc to avoid conflict with existing num_acc
def generate_unique_num_acc():
    timestamp = int(time.time() * 1000)  
    return timestamp

def test_prediction_endpoint_valid():
    # Generate a unique num_acc  
    test_data["num_acc"] =  generate_unique_num_acc()
    print(f"Generated num_acc: {test_data['num_acc']}")
    
    response = requests.post(
        url=API_GATEWAY_PREDICTION,
        auth=VALID_CREDENTIALS_ADMIN,
        json=test_data
    )
    
    assert response.status_code == 200
    response_json = response.json()
    assert "gravite_predite" in response_json
    assert response_json["gravite_predite"] == 3


def test_prediction_endpoint_invalid():
    # Generate a unique num_acc 
    test_data["num_acc"] =  generate_unique_num_acc()
     
    response = requests.post(
        url=API_GATEWAY_PREDICTION,
        auth=INVALID_CREDENTIALS,
        json=test_data 
    )
    
    assert response.status_code == 401 
    

  

    
