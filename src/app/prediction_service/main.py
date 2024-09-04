from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import os


# Définir l'application FastAPI
app = FastAPI()

# Charger le modèle
model_path = "/app/models/model_rf_clf.pkl"

if not os.path.exists(model_path):
    raise FileNotFoundError(f"Le fichier de modèle {model_path} n'existe pas.")
with open(model_path, 'rb') as model_file:
    model_data = joblib.load(model_file)
    if not isinstance(model_data, dict):
        raise ValueError("Le fichier pickle ne contient pas de dictionnaire.")
    model = model_data.get('model')
    accuracy = model_data.get('accuracy')
    if model is None or accuracy is None:
        raise ValueError("Le dictionnaire chargé ne contient pas les clés 'model' et 'accuracy'.")

class DonneesAccident(BaseModel):
    place: int
    catu: int
    trajet: float
    an_nais: int
    catv: int
    choc: float
    manv: float
    mois: int
    jour: int
    lum: int
    agg: int
    int: int
    col: float
    com: int
    dep: int
    hr: int
    mn: int
    catr: int
    circ: float
    nbv: int
    prof: float
    plan: float
    lartpc: int
    larrout: int
    situ: float

@app.post("/predict")
def predict(accident: DonneesAccident):
    """
    Endpoint pour prédire la gravité de l'accident.

    Args:
    - accident : Les données de l'accident défini selon le BaseModel

    Returns:
    - dict: La prédiction de la gravité de l'accident.
    """
    try:
        features = [
            accident.place, accident.catu, accident.trajet,
            accident.an_nais, accident.catv, accident.choc, accident.manv,
            accident.mois, accident.jour, accident.lum, accident.agg,
            accident.int, accident.col, accident.com, accident.dep,
            accident.hr, accident.mn, accident.catr, accident.circ,
            accident.nbv, accident.prof, accident.plan, accident.lartpc,
            accident.larrout, accident.situ
    ]
        prediction = model.predict([features])
        return {"Cet accident est de niveau de gravité": int(prediction[0])}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))