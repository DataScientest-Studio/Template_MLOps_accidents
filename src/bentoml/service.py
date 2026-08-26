# ----------------------------------------
# Import bibliothèques
# ----------------------------------------
import os
import bentoml
import pandas as pd
from pydantic import BaseModel, Field, ConfigDict
import time
from prometheus_client import Counter, Histogram
import mlflow
from starlette.routing import Route
from starlette.responses import Response

# ----------------------------------------
# 1. L'Infrastructure de Monitoring (Prometheus)
# ----------------------------------------

# Surveille le trafic HTTP global
REQUEST_COUNT = Counter(
    "app_requests_total",
    "Total requests",
    labelnames=["method", "endpoint", "status"]
)

# Mesure la performance globale de l'API
REQUEST_LATENCY = Histogram(
    "app_request_latency_seconds",
    "Request latency in seconds",
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0)
)

# Surveiller la distribution des prédictions
PREDICTIONS_TOTAL = Counter(
    "model_predictions_total",
    "Total predictions made",
    labelnames=["model", "status", "class"]
)

# Mesure uniquement le temps d'exécution du modèle
PREDICTION_LATENCY = Histogram(
    "model_prediction_latency_seconds",
    "Model prediction latency",
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0)
)

# ----------------------------------------
# 2. Cycle de Vie du Modèle (MLflow & BentoML) & Prédiction (/predict)
# ----------------------------------------

mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI"))
MODEL_URI = "models:/Modèle_Gravité_Accidents@champion"

class InputModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

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
    int_: int = Field(alias="int")
    atm: int
    col: int
    lat: float
    long: float
    hour: int
    nb_victim: int
    nb_vehicules: int


@bentoml.service
class PredictService:
    def __init__(self):
        self.model = mlflow.sklearn.load_model(
            "models:/Modèle_Gravité_Accidents/latest"
        )

    def _load_model(self):
        """Méthode interne pour (re)charger le modèle champion depuis MLflow."""
        try:
            self.model = mlflow.sklearn.load_model(MODEL_URI)
            print(f"Modèle chargé avec succès depuis {MODEL_URI}")
        except Exception as e:
            print(f"Modèle non trouvé ({e}). Tentative avec 'latest'...")
            try:
                self.model = mlflow.sklearn.load_model("models:/Modèle_Gravité_Accidents/latest")
                print("Modèle 'latest' chargé avec succès.")
            except Exception as e_latest:
                print(f"Aucun modèle disponible pour l'instant ({e_latest}). En attente du pipeline Airflow...")
                self.model = None

    @bentoml.api(route="/reload_model")
    def reload_model(self) -> dict:
        """Endpoint appelé par Airflow pour rafraîchir le modèle en mémoire."""
        self._load_model()
        return {"status": "success", "message": "Modèle rechargé avec succès"}

    @bentoml.api(route="/predict")
    def predict(self, input_data: InputModel) -> dict:
        """Endpoint de prédiction avec métriques"""
        start = time.perf_counter()

        # On incrémente le compteur de requêtes ici :
        REQUEST_COUNT.labels(method="POST", endpoint="/predict", status="started").inc()

        try:
            feature_names = [
                "place", "catu", "sexe", "secu1", "year_acc", "victim_age",
                "catv", "obsm", "motor", "catr", "circ", "surf", "situ", "vma",
                "jour", "mois", "lum", "dep", "com", "agg_", "int", "atm",
                "col", "lat", "long", "hour", "nb_victim", "nb_vehicules",
            ]
            x = pd.DataFrame(
                [
                    [
                        input_data.place,
                        input_data.catu,
                        input_data.sexe,
                        input_data.secu1,
                        input_data.year_acc,
                        input_data.victim_age,
                        input_data.catv,
                        input_data.obsm,
                        input_data.motor,
                        input_data.catr,
                        input_data.circ,
                        input_data.surf,
                        input_data.situ,
                        input_data.vma,
                        input_data.jour,
                        input_data.mois,
                        input_data.lum,
                        input_data.dep,
                        input_data.com,
                        input_data.agg_,
                        input_data.int_,
                        input_data.atm,
                        input_data.col,
                        input_data.lat,
                        input_data.long,
                        input_data.hour,
                        input_data.nb_victim,
                        input_data.nb_vehicules,
                    ]
                ],
                columns=feature_names,
                dtype=float,
            )

            pred = self.model.predict(x)
            
            duration = time.perf_counter() - start

            # Récupère la classe prédite (0 ou 1)
            predicted_class = str(pred[0])

            # Mise à jour des métriques
            labels_dict = {"model": "RandomForest", "status": "success", "class": predicted_class}
            PREDICTIONS_TOTAL.labels(**labels_dict).inc()
            PREDICTION_LATENCY.observe(duration)
            REQUEST_COUNT.labels(method="POST", endpoint="/predict", status="success").inc()

            return {"prediction": pred.tolist()}
        
        except Exception as e:
                labels_dict = {"model": "RandomForest", "status": "error"}
                PREDICTIONS_TOTAL.labels(**labels_dict).inc()
                REQUEST_COUNT.labels(method="POST", endpoint="/predict", status="error").inc()
                raise

# ----------------------------------------
# 4. L'Exposition des Métriques
# ----------------------------------------
    @staticmethod
    def on_asgi_app(app):
        
        async def metrics_endpoint(request):
            return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
        # Ajoute la route /metrics à l'application ASGI existante
        app.router.routes.append(Route("/metrics", metrics_endpoint, methods=["GET"]))