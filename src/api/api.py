from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import sklearn
import pandas as pd 
from sklearn import ensemble
import joblib
import numpy as np
from pydantic import BaseModel
import os
import json
import boto3
import base64


g_rf_classifier = None
g_model_filename = './src/models/trained_model.joblib'
users_directory = "./data/user_db"
users_filename = os.path.join(users_directory, "users.json")
admins_filename = os.path.join(users_directory, "admins.json")

# encoded...
AWS_ACCESS_KEY = 'QUtJQVFFRldBSlZUQjNMVDc1TlE='
AWS_SECRET_KEY = 'UFg3MHd3bXFHbkg4OEorTW5UTmhucGlWN1gydWt3NnhUU296WXk4dg=='


######  Gestion des utilisateurs et des droits (admin) ######

security = HTTPBasic()

class User(BaseModel):
    name: str
    password: str

# initialise users_file and admins_file si absents

if not os.path.exists(users_directory):
    os.makedirs(users_directory)
    print("repertoire cree")

if not os.path.isfile(users_filename):
    users = {
    "admin1": "admin1" ,
    "alice": "wonderland",
    "bob": "builder",
    "clementine": "mandarine"

    }
    with open(users_filename, 'w', encoding='utf8') as f:
        json.dump(users,f )
    print("user_json créé")

if not os.path.isfile(admins_filename):
    admins = {
    "admin1": "admin1",
    "alice": "wonderland"
    }
    with open(admins_filename, 'w', encoding='utf8') as f:
        json.dump(admins,f )
    print("admin_json créé")

# load users and admins_file
with open(users_filename, "r") as f:
    users = json.load(f)

with open(admins_filename, "r") as f:
    admins = json.load(f)

# Vérification user
def verif_user(creds: HTTPBasicCredentials = Depends(security)):
    username = creds.username
    password = creds.password
    if username in users and password == users[username]:
        return True
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )

# Vérification admin
def verif_admin(creds: HTTPBasicCredentials = Depends(security)):
    username = creds.username
    password = creds.password
    if username in admins and password == admins[username]:
        return True
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password for admin",
            headers={"WWW-Authenticate": "Basic"},
        )

#####  Gestion des prédictions #####

class Prediction(BaseModel):
    place:int
    catu:int
    sexe:int
    secu1:int
    year_acc:int
    victim_age:float
    catv:float
    obsm:float
    motor:float
    catr:int
    circ:float
    surf:float
    situ:float
    vma:float
    jour:int
    mois:int
    lum:int
    dep:int
    com:int
    agg_:int
    int:int
    atm:float
    col:float
    lat:float
    long:float
    hour:int
    nb_victim:int
    nb_vehicules:int


# def predict(features: dict) -> int:
    # """
    # Exemple format en entrée features :
    # {'place':10,
     # 'catu':3,
     # 'sexe':2,
     # 'secu1':0.0,
     # 'year_acc':2021,
     # 'victim_age':19.0,
     # 'catv':2.0,
     # 'obsm':1.0,
     # 'motor':1.0,
     # 'catr':4,
     # 'circ':2.0,
     # 'surf':1.0,
     # 'situ':1.0,
     # 'vma':30.0,
     # 'jour':4,
     # 'mois':11,
     # 'lum':5,
     # 'dep':59,
     # 'com':59350,
     # 'agg_':2,
     # 'int':2,
     # 'atm':0.0,
     # 'col':6.0,
     # 'lat':50.6325934047,
     # 'long':3.0522062542,
     # 'hour':22,
     # 'nb_victim':4,
     # 'nb_vehicules':1
    # }
    # """
    # global g_rf_classifier
    # global g_model_filename    
    # input_df = pd.DataFrame([features])
    
    ## Chargement du modèle
    # if g_rf_classifier == None:
        # g_rf_classifier = joblib.load(g_model_filename)
       
    # prediction = g_rf_classifier.predict(input_df)    
    # return int(prediction[0])   # convert np.int64 to int to avoid json exception


def predict(features: dict) -> int:
    """
    Cette version récupère le modèle dans un bucket s3
    
    Exemple format en entrée features :
    {'place':10,
     'catu':3,
     'sexe':2,
     'secu1':0.0,
     'year_acc':2021,
     'victim_age':19.0,
     'catv':2.0,
     'obsm':1.0,
     'motor':1.0,
     'catr':4,
     'circ':2.0,
     'surf':1.0,
     'situ':1.0,
     'vma':30.0,
     'jour':4,
     'mois':11,
     'lum':5,
     'dep':59,
     'com':59350,
     'agg_':2,
     'int':2,
     'atm':0.0,
     'col':6.0,
     'lat':50.6325934047,
     'long':3.0522062542,
     'hour':22,
     'nb_victim':4,
     'nb_vehicules':1
    }
    """
    global g_rf_classifier
    global g_model_filename    
    input_df = pd.DataFrame([features])
    
    # aws access, base 64 decodage
    base64_bytes = AWS_ACCESS_KEY.encode('ascii')
    message_bytes = base64.b64decode(base64_bytes)
    KEY_ID_MSG = message_bytes.decode('ascii')        
    
    base64_bytes = AWS_SECRET_KEY.encode('ascii')
    message_bytes = base64.b64decode(base64_bytes)
    SECRET_ID_MSG = message_bytes.decode('ascii')
    
    # Chargement du modèle
    if g_rf_classifier == None:
        # Configuration du client S3
        bucket_name = 'mar24accd'
        model_file = 'trained_model.joblib' 

        s3 = boto3.client('s3', region_name='eu-west-3', aws_access_key_id = KEY_ID_MSG, aws_secret_access_key = SECRET_ID_MSG)
        #s3.download_file(bucket_name, 'trained_model.joblib', './src/models/trained_model.joblib'
        #g_rf_classifier = joblib.load(g_model_filename)
        
        response = s3.get_object(Bucket=bucket_name, Key='trained_model.joblib')
        body = response['Body'].read()
        g_rf_classifier = joblib.load(io.BytesIO(body))
       
    prediction = g_rf_classifier.predict(input_df)    
    return int(prediction[0])   # convert np.int64 to int to avoid json exception    


############# Endpoints des API ###################################

api = FastAPI()

@api.get("/")
def read_root():
    return {"message": "Mars 2024 MLops Datascientest - Heroku server."}

@api.get('/status')
def get_status():
    return {'status': 'ok'}


@api.post('/prediction', tags = ['user'])
def post_prediction(prediction: Prediction, Verification = Depends(verif_user)):
    """
    Exemple test avec curl
    curl -X 'POST' 'http://127.0.0.1:8000/prediction' -H 'accept: application/json' -H 'Content-Type: application/json' -d '{"place": 0, "catu": 0, "sexe": 0, "secu1": 0, "year_acc": 0, "victim_age": 0, "catv": 0, "obsm": 0, "motor": 0, "catr": 0,  "circ": 0,  "surf": 0,  "situ": 0,  "vma": 0,  "jour": 0, "mois": 0, "lum": 0, "dep": 0, "com": 0, "agg_": 0, "int": 0, "atm": 0, "col": 0, "lat": 0, "long": 0, "hour": 0, "nb_victim": 0, "nb_vehicules": 0}'
    """    
    l_prediction = predict(prediction.dict())
    return {'prediction':l_prediction}


@api.post("/new_user", tags = ['admin'])
def create_user(new_user : User, Verifcation = Depends(verif_admin)):
    """
    Permet de poster une nouvel usager (necessite les droits admin), sous la forme suivante: 
    curl -X 'POST' 'http://localhost:8000/new_user' \
        -H 'accept: application/json' \
        -H 'Content-Type: application/json' \
        -d '{
        "name": "string",
        "password": "string"
        }'
    """

    # Si name déja présent, ne pas rajouter
    if new_user.name in users:
        raise HTTPException(
            status_code=405, 
            detail= f"name already present, choose another name")

    # Ajout du new_user dans users, renvoyer "succes"
    users.update({new_user.name : new_user.password})
    with open(users_filename, 'w', encoding='utf8') as f:
        json.dump(users,f)
    return {"user créé avec succès" : new_user}


@api.post("/new_admin", tags = ['admin'])
def create_admin(new_admin : User, Verifcation = Depends(verif_admin)):
    """
    Permet de poster une nouvel admin, sous la forme suivante: 
    curl -X 'POST' 'http://localhost:8000/new_admin' \
        -H 'accept: application/json' \
        -H 'Content-Type: application/json' \
        -d '{
        "name": "string",
        "password": "string"
        }'
    """

    # Si name déja présent dans users, ne pas rajouter
    if new_admin.name in users:
        raise HTTPException(
            status_code=405, 
            detail= f"name already present, choose another name")

    # Ajout du new_admin dans "admins" et "users", renvoyer "succes"
    users.update({new_admin.name : new_admin.password})
    admins.update({new_admin.name : new_admin.password})   

    with open(admins_filename, 'w', encoding='utf8') as f:
        json.dump(admins,f)

    with open(users_filename, 'w', encoding='utf8') as f:
        json.dump(users,f)

    return {"new admin créee avec succes" : new_admin}


# Route pour supprimer un administrateur (administrateurs seulement)
@api.delete("/delete_admin/{username}", tags=["admin"])
def remove_admin(username: str, Verification = Depends(verif_admin)):
    """
    Permet aux administrateurs de retirer les droits administrateur d'un utilisateur.
    Attention: Ne supprime pas l'utilisateur.
    Exemple de requête: 
        curl -X 'PUT' 'http://localhost:8000/remove_admin/admin_name' \
        -H 'accept: application/json' \
        -H 'Content-Type: application/json' \
        -d '{
        "admin_username": "admin1",
        "admin_password": "admin1"
        }'
    """
    if username not in admins:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cet utilisateur {username} n'est pas administrateur."
        )
    
    del admins[username]
    with open(admins_filename, 'w', encoding='utf8') as f:
        json.dump(admins,f)
    
    return {"message": f"Les droits administrateur de {username} ont été retirés avec succès."}

# Route pour supprimer un utilisateur (administrateurs seulement)
@api.delete("/delete_user/{username}", tags=["admin"])
def delete_user(username: str, Verification = Depends(verif_admin)):
    """
    Permet aux administrateurs de retirer un utilisateur.
    Message d'erreur si cet utilisateur est administrateur
    Exemple de requête: 
        curl -X 'PUT' 'http://localhost:8000/remove_admin/username2' \
        -H 'accept: application/json' \
        -H 'Content-Type: application/json' \
        -d '{
        "admin_username": "admin1",
        "admin_password": "admin1"
        }'
    """
    if username not in users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé."
        )
    
    if username in admins:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Impossible de supprimer un administrateur. Utiliser /delete_admin"
        )
    del users[username]
    with open(users_filename, 'w', encoding='utf8') as f:
        json.dump(users,f)
    return {"user supprimé avec succès" : username}





##### Endpoints de Test ###########

@api.get("/test/users and admin list", tags = ['test'])
def get_users_list():
    return {'users': users , 'admins': admins}

@api.get("/test/verify_user", dependencies=[Depends(verif_user)], tags = ['test'])
def verify_user_authorisation():
    return {"message": "User verified"}

if __name__ == '__main__':
    #
    #
    # Uniquement à des fins de debug en manuel (sans passer par le serveur FastAPI)
    #
    #    
    features_4_prediction = {'place':10,
                             'catu':3,
                             'sexe':2,
                             'secu1':0.0,
                             'year_acc':2021,
                             'victim_age':19.0,
                             'catv':2.0,
                             'obsm':1.0,
                             'motor':1.0,
                             'catr':4,
                             'circ':2.0,
                             'surf':1.0,
                             'situ':1.0,
                             'vma':30.0,
                             'jour':4,
                             'mois':11,
                             'lum':5,
                             'dep':59,
                             'com':59350,
                             'agg_':2,
                             'int':2,
                             'atm':0.0,
                             'col':6.0,
                             'lat':50.6325934047,
                             'long':3.0522062542,
                             'hour':22,
                             'nb_victim':4,
                             'nb_vehicules':1
                            }    
    ma_prediction = predict(features_4_prediction)
    print(ma_prediction)
    
    
    
    