# >>>>>>>>>> IMPORTS <<<<<<<<<<
import json
import time
import requests
import os
from pathlib import Path

# >>>>>>>>>> VARIABLES <<<<<<<<<<

delay = 5

# ---------- Paths ----------
root_path = Path(os.path.realpath(__file__)).parents[2]
path_test_features = os.path.join(root_path, "src", "models",
                                  "test_features.json")

# ----------Payloads ----------
header_admin = {"identification": "admin:4dmin"}
new_user = {"username": "sherlock", "password": "doyle", "rights": 0}
old_user = {"user": "sherlock"}

file = open(path_test_features, 'r')
test_features = json.load(file)
file.close()

model_name = {"name": "test_retrained_model"}
year_list = {"start_year": 2019, "end_year": 2020}
prediction = {"request_id": 7929238334398751, "y_true": 0}
# >>>>>>>>>> TESTS <<<<<<<<<<


# ---------- EP1: /status -----------------------------------------------------
def test_api_status():
    time.sleep(delay)
    response = requests.get(url="http://api:8000/status")
    assert response.status_code == 200
    message = "Test EP1: /status: PASSED"
    print(message)


# ---------- EP2: /add_user ---------------------------------------------------
def test_add_user():
    time.sleep(delay)
    response = requests.post(url="http://api:8000/add_user",
                             json=new_user,
                             headers=header_admin)
    assert response.status_code == 200
    message = "Test EP2: /add_user: PASSED"
    print(message)


# ---------- EP3: /remove_user ------------------------------------------------
def test_remove_user():
    time.sleep(delay)
    response = requests.delete(url="http://api:8000/remove_user",
                               json=old_user,
                               headers=header_admin)
    assert response.status_code == 200
    message = "Test EP2: /remove_user: PASSED"
    print(message)


# ---------- EP4: /predict_from_test ------------------------------------------
def test_predict_from_test():
    time.sleep(delay)
    response = requests.get(url="http://api:8000/predict_from_test",
                            headers=header_admin)
    assert response.status_code == 200
    message = "Test EP1: /status: PASSED"
    print(message)


# ---------- EP5: /predict_from_call ------------------------------------------
def test_predict_from_call():
    time.sleep(delay)
    response = requests.post(url="http://api:8000/predict_from_call",
                             json=test_features,
                             headers=header_admin)
    assert response.status_code == 200
    message = "Test EP2: /add_user: PASSED"
    print(message)


# ---------- EP6: /train ------------------------------------------------------
def test_train_model():
    time.sleep(delay)
    response = requests.post(url="http://api:8000/train",
                             json=model_name,
                             headers=header_admin)
    assert response.status_code == 200
    message = "Test EP2: /add_user: PASSED"
    print(message)


# ---------- EP7: /update_data ------------------------------------------------
def test_update_data():
    time.sleep(delay)
    response = requests.post(url="http://api:8000/update_data",
                             json=year_list,
                             headers=header_admin)
    assert response.status_code == 200
    message = "Test EP2: /add_user: PASSED"
    print(message)


# ---------- EP8: /label_prediction -------------------------------------------
def test_label_prediction():
    time.sleep(delay)
    response = requests.post(url="http://api:8000/label_prediction",
                             json=prediction,
                             headers=header_admin)
    assert response.status_code == 200
    message = "Test EP2: /add_user: PASSED"
    print(message)


# ---------- EP9: /update_f1_score --------------------------------------------
def test_update_f1_score():
    time.sleep(delay)
    response = requests.get(url="http://api:8000/update_f1_score",
                            headers=header_admin)
    assert response.status_code == 200
    message = "Test EP2: /add_user: PASSED"
    print(message)
