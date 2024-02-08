from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import numpy as np
import joblib
# from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
# Instrumentator().instrument(app).expose(app)

# Define the Accident input model
class Accident(BaseModel):
    place: int
    catu: int
    sexe: int
    secu1: float
    year_acc: int
    victim_age: int
    catv: int
    obsm: int
    motor: int
    catr: int
    circ: int
    surf: int
    situ: int
    vma: int
    jour: int
    mois: int
    lum: int
    dep: int
    com: int
    agg_: int    
    int_: int
    atm: int
    col: int
    lat: float
    long: float
    hour: int
    nb_victim: int
    nb_vehicules: int


##########################################
# Load the trained model
# model = joblib.load("../models/trained_model.joblib")
model = joblib.load("./trained_model.joblib")

##########################################
# Endpoint for predicting the severity of the accident
@app.post("/predict/")
def predict_grav(accident: Accident):

    features = np.array([accident.place, accident.catu, accident.sexe, accident.secu1, accident.year_acc,
                accident.victim_age, accident.catv, accident.obsm, accident.motor, accident.catr,
                accident.circ, accident.surf, accident.situ, accident.vma, accident.jour, accident.mois,
                accident.lum, accident.dep, accident.com, accident.agg_, accident.int_, accident.atm, accident.col,
                accident.lat, accident.long, accident.hour, accident.nb_victim, accident.nb_vehicules])
    
    features = features.reshape(1, -1)

    # Make the prediction
    prediction = model.predict(features)
    return {"prediction": prediction.tolist()}


####################################
# Root endpoint
@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <html>
    <body>
        <h1>Welcome to the Accident Severity Prediction API</h1>
    </body>
    </html>
    """


####################################
