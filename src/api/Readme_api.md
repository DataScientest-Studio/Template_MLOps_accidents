
# 1. Test /status : vérification du fonctionnement de l’API:
curl -X 'GET' 'http://127.0.0.1:8000/' -H 'accept: application/json'

# 2. Test /add_user: inscription d'un nouvel utilisateur:

curl -X 'POST' \
  'http://127.0.0.1:8000/add_user' \
  -H 'accept: application/json' \
  -H 'identification: admin:4dmin' \
  -H 'Content-Type: application/json' \
  -d '{
  "username": "sherlock",
  "password": "BakerStr33t",
  "rights": 0
}'


# 3. Test /remove_user: suppression d'un utilisateur existant:

curl -X 'DELETE' \
  'http://127.0.0.1:8000/remove_user' \
  -H 'accept: application/json' \
  -H 'identification: admin:4dmin' \
  -H 'Content-Type: application/json' \
  -d '{
  "user": "sherlock"
}'

# 4. Test /predict_from_test: prédiction à partir d'un échantillon test

curl -X 'GET' \
  'http://127.0.0.1:8000/predict_from_test' \
  -H 'accept: application/json' \
  -H 'identification: fdo:c0ps'

# 5. Test /predict_from_call: prédiction à partir du relevé d'un appel
Par défaut, les données du fichier test_features.json sont utilisées.


curl -X 'POST' \
  'http://127.0.0.1:8000/predict_from_call' \
  -H 'accept: application/json' \
  -H 'identification: fdo:c0ps' \
  -H 'Content-Type: application/json' \
  -d '{
  "place": 10,
  "catu": 3,
  "sexe": 1,
  "secu1": 0,
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
  "inter": 1,
  "atm": 0,
  "col": 6,
  "lat": 48.6,
  "long": 2.89,
  "hour": 17,
  "nb_victim": 2,
  "nb_vehicules": 1
}'

# 6. Test /train:

curl -X 'POST' \
  'http://127.0.0.1:8000/train' \
  -H 'accept: application/json' \
  -H 'identification: admin:4dmin' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "test_trained_model"
}'

  # 7. Test /update_data: 

curl -X 'POST' \
  'http://127.0.0.1:8000/update_data' \
  -H 'accept: application/json' \
  -H 'identification: admin:4dmin' \
  -H 'Content-Type: application/json' \
  -d '{
  "start_year": 2019,
  "end_year": 2020
}'

# 8. Test /label_prediction

curl -X 'POST' \
  'http://127.0.0.1:8000/label_prediction' \
  -H 'accept: application/json' \
  -H 'identification: fdo:c0ps' \
  -H 'Content-Type: application/json' \
  -d '{
  "request_id": 6012919476848551,
  "y_true": 1
}'

# 9. Test /update_f1_score

curl -X 'GET' \
  'http://127.0.0.1:8000/update_f1_score' \
  -H 'accept: application/json' \
  -H 'identification: admin:4dmin'


