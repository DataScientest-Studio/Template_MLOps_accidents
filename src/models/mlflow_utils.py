# Script de fonctions utilitaires src/models/mlflow_utils.py

import os
import mlflow
import mlflow.sklearn

#=============================================================
#   Set tracking URI
#=============================================================
def set_tracking_uri(uri: str = None):
    """
    Configure le tracking MLflow.
    Priorité à l'argument uri, sinon utilise la variable d'environnement.
    """
    if uri is None:
        uri = os.getenv("MLFLOW_TRACKING_URI")
    
    if uri is None:
        raise ValueError(
            "MLFlow_TRACKING_URI n'est pas défini."
            " Configurez-le avant d'exécuter le script ou passez-le en paramètre."
        )
    
    mlflow.set_tracking_uri(uri)
    print(f"✅ MLflow tracking URI set to: {mlflow.get_tracking_uri()}")

#=========================================================
#   Set experiment
#=========================================================
def set_experiment(experiment_name: str):
    """
    Configure l'experience MLflow
    """
    mlflow.set_experiment(experiment_name)

#=================================================================================
#   Start start_run (Version adaptée pour orchestrateur)
#=================================================================================
def start_run(run_name: str = None, run_id: str = None, nested: bool = False):
    """
    Démarrer ou reprendre un run MLflow.
    - run_id : à fournir si on veut reprendre un run existant (ex: orchestrateur).
    - nested : doit être True si on ouvre un run à l'intérieur d'un autre.
    """
    return mlflow.start_run(run_id=run_id, run_name=run_name, nested=nested)

#=========================================================
#   Log params
#=========================================================         
def log_params(params: dict):
    """
    Logger les hyperparamètres d'un modèle.
    """
    for k, v in params.items():
        mlflow.log_param(k, v)

#=========================================================
#  Log metrics
#=========================================================
def log_metrics(metrics: dict):
    """
    Logger les métriquesd'un modèle.
    """
    for k, v in metrics.items():
        mlflow.log_metric(k, v)


#=========================================================
#  Log model
#=========================================================
def log_model(model, artifact_path: str = "model"):
    """
    Logger le modèle entraîné avec mlflow.sklearn
    """
    mlflow.sklearn.log_model(model, artifact_path)

