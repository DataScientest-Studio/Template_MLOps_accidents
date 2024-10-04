from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient
import psycopg2
from psycopg2 import sql
import logging
import os

#configurer le logging
if not os.path.exists('logs'):
        os.makedirs('logs')
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(message)s",  
    handlers=[
        logging.FileHandler(f'logs/{"prediction.log"}'),  
        logging.StreamHandler() 
    ]
)
# Création d'un logger
logger = logging.getLogger(__name__)


# Définir l'application FastAPI
app = FastAPI()

# Charger le modèle
mlflow.set_tracking_uri("http://mlflow_service:5000") 
client = MlflowClient()

def load_production_model(model_name="model_rf_clf"):
    # Charger toutes les  versions du modele et chercher le tag "is_production"
    logger.info(f"Loading production model '{model_name}'...")
    try:
        versions = client.search_model_versions(f"name='{model_name}'")
    except mlflow.exceptions.RestException as e:
        logger.error(f"Model '{model_name}' not found in the registry. No production model to evaluate.")
        return None, None
    
    
    prod_model_info = None
    for version in versions:
        if version.tags.get("is_production") == "true":
            prod_model_info = version
            break

    if not prod_model_info:
        logger.error(f"No model tagged as 'is_production=true' exists for '{model_name}'.")
        return None, None
    
    prod_model_version = prod_model_info.version
    logger.info(f"Loading model version {prod_model_version} (tagged as production).")

    model_uri = f"models:/{model_name}/{prod_model_version}"

    prod_model = mlflow.pyfunc.load_model(model_uri)
    return prod_model

# On se connecte à la base de données PostgreSQL
def get_db_connection():
    conn = psycopg2.connect(
        host="db",  
        database="accidents",
        user="my_user",
        password="your_password"
    )
    return conn

class DonneesAccident(BaseModel):
    num_acc : int
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
    logger.info("start prediction...")
    model=load_production_model(model_name="model_rf_clf")
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
        gravite_predite = int(prediction[0])
        logger.info("Saving prediction in the database...")
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            insert_query = sql.SQL("""
                INSERT INTO predictions_accidents (
                    num_acc, mois, jour, lum, agg, int, col, com, dep, hr, mn,
                    catv, choc, manv, place, catu, grav, trajet, an_nais, catr,
                    circ, nbv, prof, plan, lartpc, larrout, situ
                ) VALUES (
                    {num_acc}, {mois}, {jour}, {lum}, {agg}, {int}, {col}, {com},
                    {dep}, {hr}, {mn}, {catv}, {choc}, {manv}, {place}, {catu},
                    {grav}, {trajet}, {an_nais}, {catr}, {circ}, {nbv}, {prof},
                    {plan}, {lartpc}, {larrout}, {situ}
                )
            """).format(
                num_acc=sql.Literal(accident.num_acc),
                mois=sql.Literal(accident.mois),
                jour=sql.Literal(accident.jour),
                lum=sql.Literal(accident.lum),
                agg=sql.Literal(accident.agg),
                int=sql.Literal(accident.int),
                col=sql.Literal(accident.col),
                com=sql.Literal(accident.com),
                dep=sql.Literal(accident.dep),
                hr=sql.Literal(accident.hr),
                mn=sql.Literal(accident.mn),
                catv=sql.Literal(accident.catv),
                choc=sql.Literal(accident.choc),
                manv=sql.Literal(accident.manv),
                place=sql.Literal(accident.place),
                catu=sql.Literal(accident.catu),
                grav=sql.Literal(gravite_predite),
                trajet=sql.Literal(accident.trajet),
                an_nais=sql.Literal(accident.an_nais),
                catr=sql.Literal(accident.catr),
                circ=sql.Literal(accident.circ),
                nbv=sql.Literal(accident.nbv),
                prof=sql.Literal(accident.prof),
                plan=sql.Literal(accident.plan),
                lartpc=sql.Literal(accident.lartpc),
                larrout=sql.Literal(accident.larrout),
                situ=sql.Literal(accident.situ)
            )

            cur.execute(insert_query)
            conn.commit()

            cur.close()
            conn.close()

        except Exception as db_error:
            raise HTTPException(status_code=500, detail=f"Erreur lors de l'insertion dans la base de données: {str(db_error)}")

        return {"message": "Prédiction réussie", "gravite_predite": gravite_predite}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))