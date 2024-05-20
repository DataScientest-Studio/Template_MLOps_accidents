# ---------------------------- Imports ----------------------------------------
# external
import datetime
from fastapi import FastAPI, Header, HTTPException
import pandas as pd
import joblib
import json
import os
from pathlib import Path
from pydantic import BaseModel
import random
from sklearn.metrics import f1_score
import sys
import time
from typing import Optional
import string

# internal
root_path = Path(os.path.realpath(__file__)).parents[2]
sys.path.append(os.path.join(root_path, "src", "data"))
sys.path.append(os.path.join(root_path, "src", "models"))
from update_data import data_update, data_update_without_saving
from train_model import train_and_save_model, train_without_saving

# ---------------------------- Paths ------------------------------------------
path_data_preprocessed = os.path.join(root_path, "data", "preprocessed")
path_X_train = os.path.join(path_data_preprocessed, "X_train.csv")
path_y_train = os.path.join(path_data_preprocessed, "y_train.csv")
path_X_test = os.path.join(path_data_preprocessed, "X_test.csv")
path_y_test = os.path.join(path_data_preprocessed, "y_test.csv")
path_X_test_eval = os.path.join(path_data_preprocessed, "eval_X_test.csv")
path_y_test_eval = os.path.join(path_data_preprocessed, "eval_y_test.csv")
path_logs = os.path.join(root_path, "logs")
path_db_preds_unlabeled = os.path.join(path_logs, "preds_call.jsonl")
path_db_preds_test_unlabeled = os.path.join(path_logs, "preds_test.jsonl")
path_db_preds_labeled = os.path.join(path_logs, "preds_labeled.jsonl")
path_models = os.path.join(root_path, "models")
path_trained_model = os.path.join(root_path, "models", "trained_model.joblib")
path_new_trained_model = os.path.join(root_path, "models",
                                      "new_trained_model.joblib")
path_users_db = os.path.join(root_path, "src", "users_db", "users_db.json")

# ---------------------------- HTTP Exceptions --------------------------------
responses = {
    200: {"description": "OK"},
    401: {"description": "Invalid username and/or password."}, 
    404: {"description": "File not found."}
}

# ---------------------------- Chargement base de données users ---------------
with open(path_users_db, 'r') as file:
    users_db = json.load(file)


# ---------------------------- Functions --------------------------------------
def check_user(header, rights):
    """
    Checks in users_db.json if the user has enough rights.

    Arguments:
        - header: {"identification": "username:password"}
        provided by fastapi Header module.
        - rights: int
                - 0: basic access for common users
                - 1: full access to all features.
    """
    with open(path_users_db, 'r') as file:
        users_db = json.load(file)
    try:
        user, psw = header.split(":")
    except:
        raise HTTPException(
            status_code=401,
            detail="Wrong format: you must sign following the pattern "
                   "username:password ."
        )
    try:
        users_db[user]
    except:
        raise HTTPException(
            status_code=401,
            detail="Unknown user."
        )
    if users_db[user]["password"] == psw:
        if users_db[user]["rights"] < rights:
            raise HTTPException(
                status_code=403,
                detail="Access refused: rights.")
        else:
            return True
    else:
        raise HTTPException(
                status_code=401,
                detail="Invalid password")


def get_latest_model(path):
    """
    Get latest model version.
    Args:
        - path: str, path to directory containing model files
    Returns:
        - latest model name as str
    """
    model_names = os.listdir(path)
    if '.gitkeep' in model_names:
        model_names.remove('.gitkeep')
    minor_versions = []
    for model_name in model_names:
        version = model_name.split("_")[1]
        minor_version = int(version.split(".")[1])
        minor_versions.append(minor_version)
    latest_minor = max(minor_versions)
    latest_version = "rdf_v1." + str(latest_minor) + "_shield.joblib"
    return latest_version
# ---------------------------- API --------------------------------------------


api = FastAPI(
    title="🛡️ SHIELD",
    description="API permettant l'utilisation de l'application SHIELD (Safety \
                 Hazard Identification and Emergency Law Deployment) utilisée \
                 par les forces de l'ordre pour prédire la priorité \
                 d'intervention en cas d'un accident de la route.",
    version="0.1",
    openapi_tags=[
        {'name': 'USERS',
         'description': 'Gestion des utilisateurs'},
        {'name': 'PREDICTIONS',
         'description': 'Prédictions faites par le modèle.'},
        {'name': 'UPDATE',
         'description': 'Mises à jour du modèle et des données', 
         'name': 'MONITORING',
         'description': 'Monitor model performances', 
         'name': 'DATA',
         'description': 'Extract data from logs and database'}
        ])

# ---------- 1. Check status --------------------------------------------------


@api.get('/status', name="Check status.", tags=['GET'])
async def is_fonctionnal():
    """
    Check if API is running.
    """
    return {"Shield API running well!"}

# ---------- 2. Add user: -----------------------------------------------------


class User(BaseModel):
    username: str
    password: str
    rights: Optional[int] = 0  # Droits par défaut: utilisateur fdo


@api.post('/add_user',
          name="Add new user to users database.",
          tags=['USERS'], responses=responses)
async def post_user(new_user: User, identification=Header(None)):
    """Enpoint to add new user to users database. \n
       Admin rights required. \n
       Identification: enter username and password as username:password.
    """
    if check_user(identification, 1) is True:

        # Record new user:
        users_db[new_user.username] = {
            "username": new_user.username,
            "password": new_user.password,
            "rights": new_user.rights
        }
        # Update database:
        update_users_db = json.dumps(users_db, indent=4)
        with open(path_users_db, "w") as outfile:
            outfile.write(update_users_db)

        # Return:
        return {"New user successfully added!"}

# ---------- 3. Remove user: --------------------------------------------------


class OldUser(BaseModel):
    user: str


@api.delete('/remove_user',
            name="Remove existing user.",
            tags=['USERS'], responses=responses)
async def remove_user(old_user: OldUser, identification=Header(None)):
    """Enpoint to remove existing user to users database. \n
       Admin rights required. \n
       Identification: enter username and password as username:password.
    """
    if check_user(identification, 1) is True:

        # Remove existing user:
        try:
            users_db.pop(old_user.user)
            update_users_db = json.dumps(users_db, indent=4)
            with open(path_users_db, "w") as outfile:
                outfile.write(update_users_db)
            return {"User removed!"}
        except KeyError:
            return "User doesn't exists."


# ---------- 4. Predict from test: --------------------------------------------

@api.get('/predict_from_test',
         name="Make a prediction from a line in X_test.",
         tags=['PREDICTIONS'],
         responses=responses)
async def get_pred_from_test(identification=Header(None)):
    """Enpoint to make a prediction from a single record in test pool. \n
       Fictionnal endpoint for monitoring (no real life use):
        - Split X_test in two parts : eval and pool
        - Get a single line from pool and make prediction on it.
        - Write result log in preds_test.jsonl

       Basic rights required. \n
       Identification: enter username and password as username:password.
    """
    if check_user(identification, 0) is True:

        # Get user:
        user = identification.split(":")[0]

        # TODO: Load last version of model:
        model_name = get_latest_model(path_models)
        model_path = os.path.join(path_models, model_name)
        rdf = joblib.load(model_path)

        # Load test data:
        X_test = pd.read_csv(path_X_test)
        # y_test = pd.read_csv(path_y_test)

        # Find median index
        median_index = len(X_test) // 2

        # Divide dataframe in two parts
        # X_test_eval = X_test.iloc[:median_index]
        X_test_pool = X_test.iloc[median_index:]

        # y_test_eval = y_test.iloc[:median_index]
        # y_test_pool = y_test.iloc[median_index:]

        # Select next line in X_test_pool:
        path_db_preds_test = os.path.join(path_logs, "preds_test.jsonl")

        if os.path.isfile(path_db_preds_test):
            with open(path_db_preds_test, "r") as file:
                preds_test = [json.loads(line) for line in file]
            i = preds_test[-1]['index'] + 1
        else:
            i = X_test_pool.index.tolist()[0]

        # Make prediction on selected line:
        pred_time_start = time.time()
        pred = rdf.predict(X_test_pool.loc[[i]])
        pred_time_end = time.time()

        # Create log entry:
        metadata_dictionary = {
            "request_id": "".join(random.choices(string.digits, k=16)),
            "index": i,
            "time_stamp": str(datetime.datetime.now()),
            "user_name": user,
            "context": "test",
            "response_status_code": 200,
            "output_prediction": int(pred[0]),
            "verified_prediction": None,
            "model version": model_name,
            "prediction_time": pred_time_end - pred_time_start,
            "input_features": X_test.iloc[[i]].to_dict(orient="records")[0]
            }
        metadata_json = json.dumps(obj=metadata_dictionary)

        # Export log entry:
        path_log_file = os.path.join(path_logs, "preds_test.jsonl")
        with open(path_log_file, "a") as file:
            file.write(metadata_json + "\n")

        # Response:
        priority = pred[0]
        if priority == 1:
            return "L'intervention est prioritaire."
        else:
            return "L'intervention n'est pas prioritaire."

# ---------- 5. Prédictions de priorité à partir de données saisies: ----------


class InputData(BaseModel):
    place: Optional[int] = 10
    catu: Optional[int] = 3
    sexe: Optional[int] = 1
    secu1: Optional[float] = 0.0
    year_acc: Optional[int] = 2021
    victim_age: Optional[int] = 60
    catv: Optional[int] = 2
    obsm: Optional[int] = 1
    motor: Optional[int] = 1
    catr: Optional[int] = 3
    circ: Optional[int] = 2
    surf: Optional[int] = 1
    situ: Optional[int] = 1
    vma: Optional[int] = 50
    jour: Optional[int] = 7
    mois: Optional[int] = 12
    lum: Optional[int] = 5
    dep: Optional[int] = 77
    com: Optional[int] = 77317
    agg_: Optional[int] = 2

# variable d'origine 'int' renommée ici en 'inter' (pour 'intersection')
# pour éviter les conflits avec le type 'int'.
    inter: Optional[int] = 1
    atm: Optional[int] = 0
    col: Optional[int] = 6
    lat: Optional[float] = 48.60
    long: Optional[float] = 2.89
    hour: Optional[int] = 17
    nb_victim: Optional[int] = 2
    nb_vehicules: Optional[int] = 1


@api.post('/predict_from_call',
          name="Effectue une prediction à partir de saisie opérateur.",
          tags=['PREDICTIONS'],
          responses=responses)
async def post_pred_from_call(data: InputData, identification=Header(None)):
    """Fonction pour effectuer une prédiction à partir d'une saisie effectuée
       par un agent des FdO.
       Identification: entrez votre identifiant et votre mot de passe
       au format identifiant:mot_de_passe
    """

    if check_user(identification, 0) is True:

        # Récupération de l'identifiant:
        user = identification.split(":")[0]

        # TODO: Load last version of model:
        model_name = get_latest_model(path_models)
        model_path = os.path.join(path_models, model_name)
        rdf = joblib.load(model_path)

        # Chargement des données test:
        test = pd.DataFrame.from_dict(dict(data), orient='index').T
        test.rename(columns={"inter": "int"}, inplace=True)

        # Prédiction :
        pred_time_start = time.time()
        pred = rdf.predict(test)
        pred_time_end = time.time()

        # Préparation des métadonnées pour exportation
        metadata_dictionary = {
            "request_id": "".join(random.choices(string.digits, k=16)),
            "time_stamp": str(datetime.datetime.now()),
            "user_name": user,
            "context": "call",
            "response_status_code": 200,
            "model version": model_name,
            "input_features": test.to_dict(orient="records")[0],
            "output_prediction": int(pred[0]),
            "verified_prediction": None,
            "prediction_time": pred_time_end - pred_time_start
            }
        metadata_json = json.dumps(obj=metadata_dictionary)

        # Exportation des métadonnées
        path_log_file = os.path.join(path_logs, "preds_call.jsonl")
        with open(path_log_file, "a") as file:
            file.write(metadata_json + "\n")

        # Réponse:
        priority = pred[0]
        if priority == 1:
            return "L'intervention est prioritaire."
        else:
            return "L'intervention n'est pas prioritaire."


# ---------- 6. Entraîner le modèle avec de nouvelles données: ----------------

@api.get('/train',
         name='Entrainement du modèle',
         tags=['UPDATE'])
async def get_train(identification=Header(None)):
    """Fonction pour entrainer le modèle.
    """

    if check_user(identification, 1) is True:

        # Récupération de l'identifiant:
        user = identification.split(":")[0]

        # Chargement des données pour les métadonnées:
        X_train = pd.read_csv(path_X_train)

        # Entrainement et sauvegarde du nouveau modèle:
        train_time_start = time.time()
        train_and_save_model()
        train_time_end = time.time()

        # TODO: load latest model for metadata:
        model_name = get_latest_model(path_models)
        model_path = os.path.join(path_models, model_name)
        rdf = joblib.load(model_path)

        # Préparation des métadonnées pour exportation
        metadata_dictionary = {
            "request_id": "".join(random.choices(string.digits, k=16)),
            "time_stamp": str(datetime.datetime.now()),
            "user_name": user,
            "response_status_code": 200,
            "model version": model_name,
            "estimator_type": str(type(rdf)),
            "estimator_parameters": rdf.get_params(),
            "feature_importances": dict(zip(X_train.columns.to_list(),
                                            list(rdf.feature_importances_))
                                        ),
            "train_time": train_time_end - train_time_start
            }
        metadata_json = json.dumps(obj=metadata_dictionary)

        # Exportation des métadonnées
        path_log_file = os.path.join(path_logs, "train.jsonl")
        with open(path_log_file, "a") as file:
            file.write(metadata_json + "\n")

        return {"Modèle ré-entrainé et sauvegardé!"}


# ---------- 7. Mise à jour de la base de données -----------------------------


class UpdateData(BaseModel):
    start_year: Optional[int] = 2019
    end_year: Optional[int] = 2019


@api.post('/update_data',
          name='Mise à jour des données accidents',
          tags=['UPDATE'])
async def update_data(update_data: UpdateData, identification=Header(None)):
    """
    Fonction pour mettre à jour les données accidents. \n
    Ecrase définitivement X/y_train/test.csv avec les nouvelles données
    """

    if check_user(identification, 1) is True:

        # Récupération de l'identifiant:
        user = identification.split(":")[0]

        # Create year_list:
        year_list = [update_data.start_year, update_data.end_year]

        # download, clean and preprocess data
        exec_time_start = time.time()
        data_update(year_list)
        exec_time_end = time.time()
        # Préparation des métadonnées pour exportation
        metadata_dictionary = {
            "request_id": "".join(random.choices(string.digits, k=16)),
            "time_stamp": str(datetime.datetime.now()),
            "user_name": user,
            "response_status_code": 200,
            "start_year": update_data.start_year,
            "end_year": update_data.end_year,
            "execution_time": exec_time_end - exec_time_start
            }
        metadata_json = json.dumps(obj=metadata_dictionary)
        # Exportation des métadonnées
        path_log_file = os.path.join(path_logs, "update_data.jsonl")
        with open(path_log_file, "a") as file:
            file.write(metadata_json + "\n")
        return {"Données mises à jour!"}


# -------- 8. Labellisation d'une prédiction enregistrée --------


class Prediction(BaseModel):
    """Modèle pour la labellisation d'une prédiction enregistrée"""

    request_id: int = 7929238334398751
    """Référence de la prédiction"""

    y_true: int = 1
    """Label de la prédiction"""


@api.post('/label_prediction',
          name="Labellisation d'une prédiction enregistrée",
          tags=['UPDATE'])
async def label_prediction(prediction: Prediction,
                           identification=Header(None)):
    """Fonction qui labellise une prédiction enregistrée
    à partir du retour utilisateur.

    Paramètres :
        prediction (class Prediction) : référence de la prédiction à
        labelliser et label correspondant
        identification (str) : identifiants utilisateur selon le format
        nom_d_utilisateur:mot_de_passe

    Lève :
        HTTPException401 : identifiants non valables
        HTTPException404 : enregistrement non existant

    Retourne :
        str : confirmation de la mise à jour de l'enregistrement
    """
    if check_user(identification, 0) is True:

        # Load preds_call.jsonl
        with open(path_db_preds_unlabeled, "r") as file:
            db_preds_unlabeled = [json.loads(line) for line in file]

        # Extraction de l'enregistrement correspondant au request_id reçu
        record_exists = "no"
        record_to_update = {}
        for record in db_preds_unlabeled:
            if int(record["request_id"]) == prediction.request_id:
                record_exists = "yes"
                record_to_update = record

                # Update verified_prediction with y_true
                record_to_update["verified_prediction"] = prediction.y_true

                # Mise à jour de la base de données de prédictions labellisées
                metadata_json = json.dumps(obj=record_to_update)
                with open(path_db_preds_labeled, "a") as file:
                    file.write(metadata_json + "\n")

        if record_exists == "yes":
            return {"Enregistrement mis à jour. Merci pour votre retour."}
        else:
            raise HTTPException(
                status_code=404,
                detail="Aucun enregistrement trouvé."
                       "Merci de fournir une référence (request_id) valable.")


# -------- 8bis. Labellisation d'une prédiction from test --------


@api.get('/label_pred_test',
         name="Labellisation d'une prédiction test enregistrée",
         tags=['UPDATE'])
async def label_prediction_test(identification=Header(None)):
    """Fonction qui labellise une prédiction test enregistrée
    à partir des données dans y_test.

    Lève :
        HTTPException401 : identifiants non valables
        HTTPException404 : enregistrement non existant

    Retourne :
        str : confirmation de la mise à jour de l'enregistrement
    """
    if check_user(identification, 0) is True:

        # Load preds_test.jsonl
        path_db_preds_test = os.path.join(path_logs, "preds_test.jsonl")
        with open(path_db_preds_test, "r") as file:
            preds_test = [json.loads(line) for line in file]

        # Load y_test:
        y_test = pd.read_csv(path_y_test)

        # Extraction de l'enregistrement correspondant au request_id reçu
        record_to_update = {}
        n = 0
        for j, record in enumerate(preds_test):
            if record["verified_prediction"] is None:
                n += 1
                record_to_update = record
                index = record["index"]

                # Update verified_prediction with y_true
                real_y = y_test.loc[index]['grav']
                record_to_update["verified_prediction"] = int(real_y)

                # Mise à jour de l'entrée dans preds_test.jsonl:
                preds_test[j]["verified_prediction"] = int(real_y)

                # Mise à jour de la base de données de prédictions labellisées
                metadata_json = json.dumps(obj=record_to_update)
                with open(path_db_preds_labeled, "a") as file:
                    file.write(metadata_json + "\n")

        # Mise à jour du fichier preds_test.jsonl:
        if n != 0:
            with open(path_db_preds_test, 'w') as file:
                for item in preds_test:
                    file.write(json.dumps(item) + '\n')

        return {"{number} enregistrement(s) mis à jour.".format(number=n)}

# -------- 9. Mise à jour du F1 score --------


@api.get('/update_f1_score',
         name="Mise à jour du F1 score",
         tags=['UPDATE'])
async def update_f1_score(identification=Header(None)):
    """Fonction qui calcule et enregistre le dernier F1 score du modèle
    en élargissant X_test et y_test aux nouvelles données labellisées.
    Ne modifie pas X_test.csv.

    Paramètres :
        identification (str) : identifiants administrateur selon
        le format nom_d_utilisateur:mot_de_passe

    Lève :
        HTTPException401 : identifiants non valables
        HTTPException403 : accès non autorisé

    Retourne :
        str : confirmation de la mise à jour du F1 score
    """
    if check_user(identification, 1) is True:

        # Récupération de l'identifiant:
        user = identification.split(":")[0]

        # TODO: Load last version of model:
        model_name = get_latest_model(path_models)
        model_path = os.path.join(path_models, model_name)
        rdf = joblib.load(model_path)

        # Chargement des données de test
        X_test = pd.read_csv(path_X_test)
        y_test = pd.read_csv(path_y_test)

        # Chargement de la base de données de prédictions labellisées
        with open(path_db_preds_labeled, "r") as file:
            db_preds_labeled = [json.loads(line) for line in file]
        X_test_new = pd.DataFrame()
        y_test_new = pd.Series()

        for record in db_preds_labeled:
            # Chargement des variables d'entrée dans le df X_test_new
            X_record = record["input_features"]
            X_record = {key: [value] for key, value in X_record.items()}
            X_record = pd.DataFrame(X_record)
            X_test_new = pd.concat([X_test_new, X_record])

            # Chargement des variables de sortie dans le df y_test_new
            y_record = pd.Series(record["verified_prediction"])
            if y_test_new.empty is True:
                y_test_new = y_record
            else:
                y_test_new = pd.concat([y_test_new, y_record])

        # Concaténation X/y_test et X/y_test_new:
        X_test = pd.concat([X_test, X_test_new]).reset_index(drop=True)
        y_test_new = pd.Series(y_test_new, name="grav")
        y_test = pd.concat([y_test, y_test_new]).reset_index(drop=True)

        # Prédiction générale de y
        y_pred = rdf.predict(X_test)
        y_true = y_test

        # Calcul du nouveau F1 score macro average
        f1_score_macro_average = f1_score(y_true=y_true,
                                          y_pred=y_pred,
                                          average="macro")

        # Préparation des métadonnées pour exportation
        metadata_dictionary = {
            "request_id": db_preds_labeled[-1]["request_id"],
            "time_stamp": str(datetime.datetime.now()),
            "user_name": user,
            "model version": model_name,
            "f1_score_macro_average": f1_score_macro_average}
        metadata_json = json.dumps(obj=metadata_dictionary)

        # Exportation des métadonnées
        path_log_file = os.path.join(path_logs, "f1_scores.jsonl")
        with open(path_log_file, "a") as file:
            file.write(metadata_json + "\n")
        return ("Le F1 score du modèle a été mis à jour.")

# -------- 10. Get f1-score ---------------------------------------------------


@api.get('/get_f1_score',
         name="Get f1-score",
         tags=['UPDATE'])
async def get_f1_score(identification=Header(None)):
    """
    Returns latest f1-score.
    Paramètres :
        identification (str) : identifiants administrateur selon
        le format nom_d_utilisateur:mot_de_passe

    Lève :
        HTTPException401 : identifiants non valables
        HTTPException403 : accès non autorisé

    Retourne :
        float : latest f1-score.
    """
    if check_user(identification, 1) is True:

        # Load f1_scores.jsonl
        path_db_f1_scores = os.path.join(path_logs, "f1_scores.jsonl")
        with open(path_db_f1_scores, "r") as file:
            f1_scores = [json.loads(line) for line in file]

        # Get latest f1_score:
        latest_f1 = f1_scores[-1]["f1_score_macro_average"]

        # Return:
        return {latest_f1}


# ---------- 11. Evaluate new model -------------------------------------------

@api.post("/evaluate_new_model",
          name="Evaluate new model",
          tags=["MONITORING"]
          )
async def post_new_model_score(update_data: UpdateData,
                               identification=Header(None)):
    """
    Triggers:
        - update data by adding a new year
        - train model on new data
        - evaluate model
    Returns: new_f1_score
    Does not overwrite anything.
    """
    if check_user(identification, 1) is True:

        # Create year_list:
        year_list = [update_data.start_year, update_data.end_year]

        # Update data without saving:
        data_update_without_saving(year_list)

        # Get new model:
        rdf = train_without_saving()

        # ----- Evaluate new model ----- :

        # Chargement des données de test:
        X_test = pd.read_csv(path_X_test_eval)
        y_test = pd.read_csv(path_y_test_eval)

        # Prédiction générale de y
        y_pred = rdf.predict(X_test)
        y_true = y_test

        # Calcul du nouveau F1 score macro average
        new_f1_score_macro_average = f1_score(y_true=y_true,
                                              y_pred=y_pred,
                                              average="macro")
        # TODO: Erase all eval_ files

        # Return:
        return {new_f1_score_macro_average}


# -------------- 12. Get all users --------------------------------------------

@api.get("/get_users",
          name="Get all users",
          tags=["DATA"]
          )
async def get_all_users(identification=Header(None)):
    """
    Endpoint to get users_db in json format.
    Needs admin authorization.
    """
    if check_user(identification, 1) is True:
        with open(path_users_db, 'r') as file:
            users_db = json.load(file)
        return users_db

# -------------- 13. Get logs --------------------------------------------


class LogFile(BaseModel):
    name: str


@api.post("/get_logs",
          name="Get logs",
          tags=["DATA"]
          )
async def get_logs(file: LogFile,
                   identification=Header(None)):
    """
    Endpoint to get logs in jsonl format.
    Needs admin authorization.
    Args: str, one of these names:
        - f1_score
        - preds_call
        - preds_labelled
        - preds_test
        - train
        - update_data
    """
    if check_user(identification, 1) is True:
        # Get filenames from logs folder:
        filenames = os.listdir(path_logs)

        # Check if file exists:
        filename = f"{file.name}.jsonl"
        if filename in filenames:
            path_to_file = os.path.join(path_logs, filename)
            with open(path_to_file, 'r') as file:
                requested_file = [json.loads(line) for line in file]

            return requested_file

        else:
            raise HTTPException(
                status_code=404,
                detail="File doesn't exists.")
