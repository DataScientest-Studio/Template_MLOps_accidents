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


g_rf_classifier = None
g_model_filename = './src/models/trained_model.joblib'
#g_model_filename = 'D:/Development/Python/mar24_cmlops_accidents/src/models/trained_model.joblib'
#g_model_filename = '../models/trained_model.joblib'


####  Gestion des utilisateurs et des droits (admin) #####

security = HTTPBasic()

class User(BaseModel):
    name: str
    password: str

# initialise users and admins
users = {
  "alice": "wonderland",
  "bob": "builder",
  "clementine": "mandarine",
  "admin1": "admin1" 
}
admins = {
  "admin1": "admin1" 
}

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
        print("Admin Validated")
        return True
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password for admin",
            headers={"WWW-Authenticate": "Basic"},
        )

####  Gestion des prédictions #####

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


def predict(features: dict) -> int:
    """
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
    
    # Chargement du modèle
    if g_rf_classifier == None:
        g_rf_classifier = joblib.load(g_model_filename)
       
    prediction = g_rf_classifier.predict(input_df)    
    return int(prediction[0])   # convert np.int64 to int to avoid json exception


############# Endpoints des API ###################################

api = FastAPI()

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
    global users

    # Si name déja présent, ne pas rajouter
    if new_user.name in users:
        raise HTTPException(
            status_code=405, 
            detail= f"name already present, choose another name")

    # Ajout du new_user dans users, renvoyer "succes"
    users.update({new_user.name : new_user.password})
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
    global users, admins

    # Si name déja présent dans users, ne pas rajouter
    if new_admin.name in users:
        raise HTTPException(
            status_code=405, 
            detail= f"name already present, choose another name")

    # Ajout du new_admin dans "admins" et "users", renvoyer "succes"

    users.update({new_admin.name : new_admin.password})
    admins.update({new_admin.name : new_admin.password})   

    return {"new admin créee avec succes" : new_admin}

@api.get('test/users and admin list', tags = ['test'])
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
    
    
    
    