import os
from fastapi.testclient import TestClient
from fastapi import status, FastAPI
import joblib
from unittest.mock import Mock, patch, MagicMock
import numpy as np

# from model_api.api import api, users_db, ADMIN_USERNAME, ADMIN_PASSWORD, hash_password

# ADMIN_USERNAME = "admin"
# ADMIN_PASSWORD = "adm1n"

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")


url = "http://localhost:8001/user/login"

client = TestClient(FastAPI())

ADMIN_USER = (ADMIN_USERNAME, {"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})

response = client.get("/")

print("response = ", response)


def login_as_admin():

    response = client.post(
        "/user/login", json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
    )

    login_data = response.json()
    print("logindata ###########################", login_data)
    access_token = login_data["access_token"]

    # Access the secured endpoint with the access token

    return access_token


# function to test the prediction


def refresh_api():

    login_response = client.post(
        "/refresh", json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
    )

    login_data = login_response.json()

    access_token = login_data["access_token"]

    # this is the testfeatures provided in test_features.json
    test_features = {
        "place": 10,
        "catu": 3,
        "sexe": 1,
        "secu1": 0.0,
        "year_acc": 2021,
        "victim_age": 60,
        "catv": 2,
        "obsm": 1,
        "motor": 1,
        "catr": 3,
        "circ": 2,
        "surf": 1,
        "situ": 1,
        "vma": 50,
        "jour": 7,
        "mois": 12,
        "lum": 5,
        "dep": 77,
        "com": 77317,
        "agg_": 2,
        "int": 1,
        "atm": 1,
        "col": 6,
        "lat": 48.60,
        "long": 2.89,
        "hour": 17,
        "nb_victim": 2,
        "nb_vehicules": 1,
    }

    # defining the header with the previously created access token
    headers = {"Authorization": f"Bearer {access_token}"}
    prediction_response = client.post("/predict", json=test_features, headers=headers)

    # Assert the response status code to be 200
    assert prediction_response.status_code == status.HTTP_200_OK

    # Optionally, you can check the response content
    prediction_response_json = prediction_response.json()
    return prediction_response_json


login_as_admin()
