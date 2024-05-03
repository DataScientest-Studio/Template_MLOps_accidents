# external
from fastapi.testclient import TestClient
import json
import os
from pathlib import Path
import sys
import unittest

# internal:
root_path = Path(os.path.realpath(__file__)).parents[2]
sys.path.append(os.path.join(root_path, "src", "api"))
from api import api

# paths
# path_users_db = os.path.join(root_path, "src", "api", "users_db.json")
path_test_features = os.path.join(root_path, "src", "models",
                                  "test_features.json")

# Charger les données de test_features.json
file = open(path_test_features, 'r')
test_features = json.load(file)
file.close()

# Création d'un client de test pour notre API
client = TestClient(api)


class TestAPI(unittest.TestCase):
    def test_is_functional(self):
        # EP 1
        response = client.request(method="GET",
                                  url='/status')
        # Check response (code 200)
        self.assertTrue(response.status_code == 200, "EP1 /status: FAILED")
        print("EP1 /status: PASSED")

    def test_add_user(self):
        new_user_data = {"username": "test_user", "password": "test_password"}
        # EP 2
        response = client.request(method="POST", url='/add_user',
                                  json=new_user_data,
                                  headers={"identification": "admin:4dmin"})
        # Check response (code 200)
        self.assertTrue(response.status_code == 200, "EP2 /add_user: FAILED")
        print("EP2 /add_user: PASSED")

    def test_remove_user(self):
        old_user_data = {"user": "test_user"}
        # EP 3
        response = client.request(method="DELETE", url='/remove_user',
                                  json=old_user_data,
                                  headers={"identification": "admin:4dmin"})
        # Check response (code 200)
        self.assertTrue(response.status_code == 200,
                        "EP3 /remove_user: FAILED")
        print("EP3 /remove_user: PASSED")

    def test_predict_from_test(self):
        # EP 4
        response = client.request(method="GET",
                                  url='/predict_from_test',
                                  headers={"identification": "fdo:c0ps"})
        # Check response (code 200)
        self.assertTrue(response.status_code == 200,
                        "EP4 /predict_from_test: FAILED")
        print("EP4 /predict_from_test: PASSED")

    def test_predict_from_call(self):
        # EP 5
        response = client.request(method="POST",
                                  url='/predict_from_call',
                                  json=test_features,
                                  headers={"identification": "admin:4dmin"})
        # Check response (code 200)
        self.assertTrue(response.status_code == 200,
                        "EP5 /predict_from_call: FAILED")
        print("EP5 /predict_from_call: PASSED")

    def test_train_model(self):
        # EP 6
        response = client.request(method="GET",
                                  url='/train',
                                  headers={"identification": "admin:4dmin"})
        # Check response (code 200)
        self.assertTrue(response.status_code == 200,
                        "EP6 /train: FAILED")
        print("EP6 /train: PASSED")

    def test_update_data(self):
        year_list = {"start_year": 2019, "end_year": 2020}
        # EP 7
        response = client.request(method="POST",
                                  url='/update_data',
                                  json=year_list,
                                  headers={"identification": "admin:4dmin"})
        # Check response (code 200)
        self.assertTrue(response.status_code == 200,
                        "EP7 /update_data: FAILED")
        print("EP7 /update_data: PASSED")

    def test_label_prediction(self):
        """Test unitaire pour l'endpoint /label_prediction"""

        # Définition des données d'entrée
        prediction = {"request_id": 7929238334398751,
                      "y_true": 0}
        header = {"identification": "fdo:c0ps"}

        # EP 8
        response = client.request(method="POST",
                                  url='/label_prediction',
                                  json=prediction,
                                  headers=header)

        # Check response (code 200)
        self.assertTrue(response.status_code == 200,
                        "EP8 /label_prediction: FAILED")
        print("EP8 /label_prediction: PASSED")

    def test_update_f1_score(self):
        """Test unitaire pour l'endpoint /update_f1_score"""

        # Définition des données d'entrée
        header = {"identification": "admin:4dmin"}

        # EP 9
        response = client.request(method="GET",
                                  url='/update_f1_score',
                                  headers=header)

        # Check response (code 200)
        self.assertTrue(response.status_code == 200,
                        "EP9 /update_f1_score: FAILED")
        print("EP9 /update_f1_score: PASSED")


if __name__ == '__main__':
    # Exécution des tests unitaires
    unittest.main()
