# ---------- Imports -------------------------------------------------------- #
import requests

# ---------- Payloads ------------------------------------------------------- #
header_admin = {"identification": "admin:4dmin"}
year_list = {"start_year": 2019, "end_year": 2019}
new_model = {"name": "new_trained_model"}
localhost = "127.0.0.1"  # TODO: change localhost into api for docker

# ---------- Get last f1_score ---------------------------------------------- #
response = requests.get(url=f"http://{localhost}:8000/get_f1_score",
                        headers=header_admin)
f1_score = response.json()[0]

# ---------- Proceed monitoring --------------------------------------------- #
f1_threshold = 0.744

if f1_score < f1_threshold:
    # Get new f1_score with updated data:
    response = requests.post(url=f"http://{localhost}:8000/evaluate_new_model",
                             json=year_list,
                             headers=header_admin)
    new_f1_score = response.json()[0]

    # Update and save new model if necessary:
    if new_f1_score > f1_score:
        response = requests.post(url=f"http://{localhost}:8000/update_data",
                                 json=year_list,
                                 headers=header_admin)
        print(response.json()[0])

        response = requests.post(url=f"http://{localhost}:8000/train",
                                 json=new_model,
                                 headers=header_admin)
        print(response.json()[0])
# TODO: request update f1_score
    else:
        print("Data and model successfully updated. \n"
              f"New f1_score: {new_f1_score} .")

else:
    print(f"Actual f1_score: {f1_score}. \n"
          f"f1 threshold: {f1_threshold}. \n"
          "There is no need to update model yet.")
