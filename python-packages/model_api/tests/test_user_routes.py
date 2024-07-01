import os
from fastapi.testclient import TestClient
from fastapi import status
import joblib
from unittest.mock import Mock, patch, MagicMock
import numpy as np

# Mocking the `joblib` module so no model needed for the unit tests
mock_joblib_load = patch.object(joblib, "load", return_value=MagicMock()).start()

os.environ['ADMIN_USERNAME'] = "the_admin_username"
os.environ['ADMIN_PASSWORD'] = "the_admin_password"

from model_api.api import api, users_db, ADMIN_USERNAME, ADMIN_PASSWORD, hash_password

client = TestClient(api)

UNKNOWN_USER = ("unknown", "user")
NON_ADMIN_USER = list(users_db.items())[0]
ADMIN_USER = (ADMIN_USERNAME, {"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})


def test_root():
    """Testing if the root endpoint works"""
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK


def test_unauthorized_login():
    """Testing if secured endpoint doesnt work because it has no auth."""
    response = client.get("/secured")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_unknown_user_login():
    """Testing the secured endpoint doesnt work because of unknown user."""
    response = client.get("/secured", auth=UNKNOWN_USER)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_login_with_known_user():
    """Testing the userlogin endpoint works with non admin."""
    response = client.post(
        "/user/login", json={"username": "testuser", "password": "testpassword"}
    )
    assert response.status_code == status.HTTP_200_OK


def test_login_as_admin():
    """Testing the secured endpoint works with admin user."""
    # hashed_password_admin = hash_password(ADMIN_PASSWORD)
    response = client.post(
        "/user/login", json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
    )
    assert response.status_code == status.HTTP_200_OK

    login_data = response.json()
    assert "access_token" in login_data

    access_token = login_data["access_token"]

    # Access the secured endpoint with the access token
    secured_response = client.get(
        "/secured", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert secured_response.status_code == status.HTTP_200_OK


#function to test the prediction
@patch("model_api.api.joblib")
def test_prediction(load_model_mock):
    #mocking the joblib predict function
    load_model_mock.predict.return_value = np.asarray([1])

    hashed_password_admin = hash_password(ADMIN_PASSWORD)
    login_response = client.post("/user/login",json= {"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
    assert login_response.status_code == status.HTTP_200_OK

    #checking if we get an access token and saving it in the variable access token
    login_data = login_response.json()
    assert "access_token" in login_data
    access_token = login_data["access_token"]

    #this is the testfeatures provided in test_features.json
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
            "nb_vehicules": 1
            }

    #defining the header with the previously created access token
    headers = {"Authorization": f"Bearer {access_token}"}
    prediction_response = client.post("/predict", json=test_features, headers=headers)

    # Assert the response status code to be 200
    assert prediction_response.status_code == status.HTTP_200_OK

    # Optionally, you can check the response content
    prediction_response_json =  prediction_response.json()
    assert "prediction" in  prediction_response_json
