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
# from sklearn import ensemble
from sklearn.metrics import f1_score
import sys
import time
from typing import Optional
# import numpy as np
import string

# internal
# add path to import datalib which is in src/data
# 3 folders upper of the current
root_path = Path(os.path.realpath(__file__)).parents[2]
sys.path.append(os.path.join(root_path, "src", "data"))
sys.path.append(os.path.join(root_path, "src", "models"))
from update_data import data_update
from train_model import train_and_save_model

# ---------------------------- Paths ------------------------------------------
path_data_preprocessed = os.path.join(root_path, "data", "preprocessed")
path_X_train = os.path.join(path_data_preprocessed, "X_train.csv")
path_y_train = os.path.join(path_data_preprocessed, "y_train.csv")
path_X_test = os.path.join(path_data_preprocessed, "X_test.csv")
path_y_test = os.path.join(path_data_preprocessed, "y_test.csv")
path_logs = os.path.join(root_path, "logs")
path_db_preds_unlabeled = os.path.join(path_logs, "preds_call.jsonl")
path_db_preds_test_unlabeled = os.path.join(path_logs, "preds_test.jsonl")
path_db_preds_labeled = os.path.join(path_logs, "preds_labeled.jsonl")
path_trained_model = os.path.join(root_path, "models", "trained_model.joblib")
path_new_trained_model = os.path.join(root_path, "models",
                                      "new_trained_model.joblib")
path_users_db = os.path.join(root_path, "src", "users_db", "users_db.json")

# ---------------------------- HTTP Exceptions --------------------------------
responses = {
    200: {"description": "OK"},
    401: {"description": "Identifiant ou mot de passe invalide(s)"}
}

# ---------------------------- Chargement base de données users ---------------
with open(path_users_db, 'r') as file:
    users_db = json.load(file)

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
         'description': 'Mises à jour du modèle et des données'}
        ])

# ---------- 1. Vérification du fonctionnement de l’API: ----------------------


@api.get('/status', name="test de fonctionnement de l'API", tags=['GET'])
async def is_fonctionnal():
    """
    Vérifie que l'api fonctionne.
    """
    return {"L'api fonctionne."}

# ---------- 2. Inscription d'un utilisateur: ---------------------------------


class User(BaseModel):
    username: str
    password: str
    rights: Optional[int] = 0  # Droits par défaut: utilisateur fdo


@api.post('/add_user',
          name="Ajout d'un nouvel utilisateur",
          tags=['USERS'], responses=responses)
async def post_user(new_user: User, identification=Header(None)):
    """Fonction pour ajouter un nouvel utilisateur.
       Il faut être administrateur pour pouvoir ajouter un nouvel utilisateur.
       Identification: entrez votre identifiant et votre mot de passe
       au format identifiant:mot_de_passe
    """
    # Récupération des identifiants et mots de passe:
    user, psw = identification.split(":")

    # Test d'autorisation:
    if users_db[user]['rights'] == 1:

        # Test d'identification:
        if users_db[user]['password'] == psw:

            # Enregistrement du nouvel utilisateur:
            users_db[new_user.username] = {
                "username": new_user.username,
                "password": new_user.password,
                "rights": new_user.rights
            }
            update_users_db = json.dumps(users_db, indent=4)
            with open(path_users_db, "w") as outfile:
                outfile.write(update_users_db)

            return {"Nouvel utilisateur ajouté!"}

        else:
            raise HTTPException(
                status_code=401,
                detail="Identifiant ou mot de passe invalide(s)")
    else:
        raise HTTPException(
                status_code=403,
                detail="Vous n'avez pas les droits d'administrateur.")


# ---------- 3. Suppresion d'un utilisateur: ----------------------------------


class OldUser(BaseModel):
    user: str


@api.delete('/remove_user',
            name="Suppression d'un utilisateur existant.",
            tags=['USERS'], responses=responses)
async def remove_user(old_user: OldUser, identification=Header(None)):
    """Fonction pour supprimer un nouvel utilisateur.
       Il faut être administrateur pour pouvoir supprimer un nouvel
       utilisateur.
       Identification: entrez votre identifiant et votre mot de passe
       au format identifiant:mot_de_passe
    """
    # Récupération des identifiants et mots de passe:
    user, psw = identification.split(":")

    # Test d'autorisation:
    if users_db[user]['rights'] == 1:

        # Test d'identification:
        if users_db[user]['password'] == psw:

            # Suppression de l'ancien utilisateur:
            try:
                users_db.pop(old_user.user)
                update_users_db = json.dumps(users_db, indent=4)
                with open(path_users_db, "w") as outfile:
                    outfile.write(update_users_db)
                return {"Utilisateur supprimé!"}

            except KeyError:
                return "L'utilisateur spécifié n'existe pas."

        else:
            raise HTTPException(
                status_code=401,
                detail="Identifiant ou mot de passe invalide(s)")
    else:
        raise HTTPException(
                status_code=403,
                detail="Vous n'avez pas les droits d'administrateur.")


# ---------- 4. Prédictions de priorité à partir des données test: ------------

@api.get('/predict_from_test',
         name="Effectue une prediction à partir d'un échantillon test.",
         tags=['PREDICTIONS'],
         responses=responses)
async def get_pred_from_test(identification=Header(None)):
    """Fonction pour effectuer une prédiction à partir d'une donnée
        issue de l'échantillon de test.
        Identification: entrez votre identifiant et votre mot de passe
        au format identifiant:mot_de_passe
    """
    # Récupération des identifiants et mots de passe:
    user, psw = identification.split(":")

    # Test d'identification:
    if users_db[user]['password'] == psw:

        # Chargement du modèle:
        rdf = joblib.load(path_trained_model)

        # Chargement des données test:
        X_test = pd.read_csv(path_X_test)
        # y_test = pd.read_csv(path_y_test)

        # Trouver l'index médian
        median_index = len(X_test) // 2

        # Diviser le DataFrame en deux parties
        # X_test_eval = X_test.iloc[:median_index]
        X_test_pool = X_test.iloc[median_index:]

        # y_test_eval = y_test.iloc[:median_index]
        # y_test_pool = y_test.iloc[median_index:]

        # Sélection de la donnée suivante dans X_test_pool:
        path_db_preds_test = os.path.join(path_logs, "preds_test.jsonl")
        with open(path_db_preds_test, "r") as file:
            preds_test = [json.loads(line) for line in file]
            if preds_test != []:
                i = preds_test[-1]['index'] + 1
            else:
                i = X_test_pool.index.tolist()[0]

        # Prédiction de la donnée sélectionnée:
        pred_time_start = time.time()
        pred = rdf.predict(X_test_pool.loc[[i]])
        pred_time_end = time.time()

        # Préparation des métadonnées pour exportation
        metadata_dictionary = {
            "request_id": "".join(random.choices(string.digits, k=16)),
            "index": i,
            "time_stamp": str(datetime.datetime.now()),
            "user_name": user,
            "context": "test",
            "response_status_code": 200,
            "output_prediction": int(pred[0]),
            "verified_prediction": None,
            "prediction_time": pred_time_end - pred_time_start,
            "input_features": X_test.iloc[[i]].to_dict(orient="records")[0]
            }
        metadata_json = json.dumps(obj=metadata_dictionary)

        # Exportation des métadonnées
        path_log_file = os.path.join(path_logs, "preds_test.jsonl")
        with open(path_log_file, "a") as file:
            file.write(metadata_json + "\n")

        # Réponse:
        priority = pred[0]
        if priority == 1:
            return "L'intervention est prioritaire."
        else:
            return "L'intervention n'est pas prioritaire."

    else:
        raise HTTPException(
            status_code=401,
            detail="Identifiant ou mot de passe invalide(s)"
        )

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
    # Récupération des identifiants et mots de passe:
    user, psw = identification.split(":")

    # Test d'identification:
    if users_db[user]['password'] == psw:

        # Chargement du modèle:
        rdf = joblib.load(path_trained_model)

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

    else:
        raise HTTPException(
            status_code=401,
            detail="Identifiant ou mot de passe invalide(s)"
        )


# ---------- 6. Entraîner le modèle avec de nouvelles données: ----------------

class UpdateModel(BaseModel):
    name: Optional[str] = "test_trained_model"


@api.post('/train',
          name='Entrainement du modèle',
          tags=['UPDATE'])
async def post_train(new_model: UpdateModel,
                     identification=Header(None)):
    """Fonction pour entrainer le modèle.
    """
# Récupération des identifiants et mots de passe:
    user, psw = identification.split(":")

    # Test d'autorisation:
    if users_db[user]['rights'] == 1:

        # Test d'identification:
        if users_db[user]['password'] == psw:

            # Chargement des données pour les métadonnées:
            X_train = pd.read_csv(path_X_train)

            # Entrainement et sauvegarde du nouveau modèle:
            train_time_start = time.time()
            train_and_save_model(model_name=new_model.name)
            train_time_end = time.time()

            # Chargement du nouveau modèle:
            path_new_trained_model = os.path.join(root_path,
                                                  "models",
                                                  f"{new_model.name}.joblib")
            rdf = joblib.load(path_new_trained_model)

            # Préparation des métadonnées pour exportation
            metadata_dictionary = {
                "request_id": "".join(random.choices(string.digits, k=16)),
                "time_stamp": str(datetime.datetime.now()),
                "user_name": user,
                "response_status_code": 200,
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

        else:
            raise HTTPException(
                status_code=401,
                detail="Identifiant ou mot de passe invalide(s)")
    else:
        raise HTTPException(
                status_code=403,
                detail="Vous n'avez pas les droits d'administrateur.")

# ---------- 7. Mise à jour de la base de données -----------------------------


class UpdateData(BaseModel):
    start_year: Optional[int] = 2019
    end_year: Optional[int] = 2020


# post ou put?
@api.post('/update_data',
          name='Mise à jour des données accidents',
          tags=['UPDATE'])
async def update_data(update_data: UpdateData, identification=Header(None)):
    """Fonction pour mettre à jour les données accidents.
    """
    # Récupération des identifiants et mots de passe:
    user, psw = identification.split(":")

    # Create year_list:
    year_list = [update_data.start_year, update_data.end_year]

    # Test d'autorisation:
    if users_db[user]['rights'] == 1:

        # Test d'identification:
        if users_db[user]['password'] == psw:

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

        else:
            raise HTTPException(
                status_code=401,
                detail="Identifiant ou mot de passe invalide(s)")
    else:
        raise HTTPException(
                status_code=403,
                detail="Vous n'avez pas les droits d'administrateur.")

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
    # Récupération des identifiants
    user, psw = identification.split(":")

    # Test d'identification
    if users_db[user]['password'] == psw:

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
            raise HTTPException(status_code=404,
                                detail="Aucun enregistrement trouvé. Merci de fournir une référence (request_id) valable.")

    else:
        raise HTTPException(status_code=401,
                            detail="Identifiants non valables.")

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
    # Récupération des identifiants
    user, psw = identification.split(":")

    # Test d'identification
    if users_db[user]['password'] == psw:

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
    else:
        raise HTTPException(status_code=401,
                            detail="Identifiants non valables.")

# -------- 9. Mise à jour du F1 score --------


@api.get('/update_f1_score',
         name="Mise à jour du F1 score",
         tags=['UPDATE'])
async def update_f1_score(identification=Header(None)):
    """Fonction qui calcule et enregistre le dernier F1 score du modèle
    en élargissant X_test et y_test aux nouvelles données labellisées

    Paramètres :
        identification (str) : identifiants administrateur selon
        le format nom_d_utilisateur:mot_de_passe

    Lève :
        HTTPException401 : identifiants non valables
        HTTPException403 : accès non autorisé

    Retourne :
        str : confirmation de la mise à jour du F1 score
    """
    # Récupération des identifiants
    user, psw = identification.split(":")

    # Test d'autorisation
    if users_db[user]['rights'] == 1:

        # Test d'identification
        if users_db[user]['password'] == psw:

            # Chargement du modèle
            rdf = joblib.load(path_trained_model)

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
                if y_test_new.empty is True:  # Pour éviter l'avertissement suivant : « FutureWarning: The behavior of array concatenation with empty entries is deprecated. »
                    y_test_new = y_record
                else:
                    y_test_new = pd.concat([y_test_new, y_record])

            # Consolidation des données pour la prédiction générale
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
                "f1_score_macro_average": f1_score_macro_average}
            metadata_json = json.dumps(obj=metadata_dictionary)

            # Exportation des métadonnées
            path_log_file = os.path.join(path_logs, "f1_scores.jsonl")
            with open(path_log_file, "a") as file:
                file.write(metadata_json + "\n")

            return ("Le F1 score du modèle a été mis à jour.")

        else:
            raise HTTPException(status_code=401,
                                detail="Identifiants non valables.")

    else:
        raise HTTPException(status_code=403,
                            detail="Vous n'avez pas les droits d'administrateur.")
    
# -------- 10. Get f1-score --------


@api.get('/get_f1_score',
         name="Get f1-score",
         tags=['UPDATE'])
async def get_f1_score(identification=Header(None)):
    """Returns latest f1-score.
    Paramètres :
        identification (str) : identifiants administrateur selon
        le format nom_d_utilisateur:mot_de_passe

    Lève :
        HTTPException401 : identifiants non valables
        HTTPException403 : accès non autorisé

    Retourne :
        float : latest f1-score.
    """
    # Récupération des identifiants
    user, psw = identification.split(":")

    # Test d'autorisation
    if users_db[user]['rights'] == 1:

        # Test d'identification
        if users_db[user]['password'] == psw:

            # Load f1_scores.jsonl
            path_db_f1_scores = os.path.join(path_logs, "f1_scores.jsonl")
            with open(path_db_f1_scores, "r") as file:
                f1_scores = [json.loads(line) for line in file]

            # Get latest f1_score:
            latest_f1 = f1_scores[-1]["f1_score_macro_average"]

            # Return:
            return {latest_f1}

        else:
            raise HTTPException(status_code=401,
                                detail="Identifiants non valables.")

    else:
        raise HTTPException(status_code=403,
                            detail="Vous n'avez pas les droits d'administrateur.")

