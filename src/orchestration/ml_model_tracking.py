import mlflow
from datetime import date

mlflow.set_tracking_uri("http://localhost:8080")
mlflow.set_experiment("accidents_experiment")
