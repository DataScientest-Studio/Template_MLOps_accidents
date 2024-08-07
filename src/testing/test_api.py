import pytest
from fastapi.testclient import TestClient
import sys
import os
import warnings

# Ajoutez le chemin du module au sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))
from app.main import app 

client = TestClient(app)

# Tests pour la route de root avec des informations d'identification valides
def test_get_root():
    response = client.get("/", auth=("user1", "datascientest"))
    assert response.status_code == 200
    assert response.json() == {"message": "Bienvenue sur notre application de prédiction d'accident, Sousou!"}

# Tests pour la route de root avec des informations d'identification invalides.
def test_access_root_with_incorrect_identifiant():
    response = client.get("/", auth=("user4", "wrongpassword"))
    assert response.status_code == 401
    assert response.json() == {"detail": "Identifiant ou mot de passe incorrect"}


# Tests pour la route de prédiction avec des données valides
def test_post_predict_valid_data():
    accident_data = {
        "place": 1, "catu": 1, "trajet": 9.0, "an_nais": 1951,
        "catv": 7, "choc": 7.0, "manv": 1.0, "mois": 1,
        "jour": 28, "lum": 1, "agg": 1, "int": 1, "col": 6.0,
        "com": 82, "dep": 590, "hr": 0, "mn": 0, "catr": 3,
        "circ": 1.0, "nbv": 2, "prof": 1.0, "plan": 1.0,
        "lartpc": 0, "larrout": 70, "situ": 5.0
    }

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="X does not have valid feature names")
        response = client.post("/predict", json=accident_data, auth=("user1", "datascientest"))
    
    assert response.status_code == 200
    assert "Cet accident est de niveau de gravtité " in response.json()
    assert response.json()["Cet accident est de niveau de gravtité "] == 2


# Tests pour la route de prédiction avec des données invalides
def test_post_predict_invalid_data():
    accident_data = {
        "place": "a", "catu": 1, "trajet": 9.0, "an_nais": 1951,
        "catv": 7, "choc": 7.0, "manv": 1.0, "mois": 1,
        "jour": 28, "lum": 1, "agg": 1, "int": 1, "col": 6.0,
        "com": 82, "dep": 590, "hr": 0, "mn": "b", "catr": 3,
        "circ": 1.0, "nbv": 2, "prof": 1.0, "plan": 1.0,
        "lartpc": 0, "larrout": 70, "situ": 5.0
    }

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="X does not have valid feature names")
        response = client.post("/predict", json=accident_data, auth=("user1", "datascientest"))
    
    assert response.status_code == 422
    

# Tests pour la route d'accuracy avec auth invalide
def test_get_accuracy_as_user():
    response = client.get("/accuracy", auth=("user1", "datascientest"))
    assert response.status_code == 403  


# Tests pour la route d'accuracy avec auth valide
def test_get_accuracy_as_admin():
    response = client.get("/accuracy", auth=("admin", "adminsecret"))
    assert response.status_code == 200
    accuracy_data = response.json()
    assert isinstance(accuracy_data, dict)
    assert len(accuracy_data) == 1
    accuracy_value = list(accuracy_data.values())[0]
    assert isinstance(accuracy_value, (int, float))
    assert accuracy_value > 0.6