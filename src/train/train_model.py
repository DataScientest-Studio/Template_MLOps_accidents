import os
import sklearn
import pandas as pd
from sklearn import ensemble
import numpy as np
import mlflow
import mlflow.sklearn

# Configuration de MLFlow
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
mlflow.set_tracking_uri(MLFLOW_URI)
mlflow.set_experiment("Gravité_Accidents")

DATA_DIR = os.getenv("DATA_DIR", "/app/data/preprocessed")

X_train = pd.read_csv(os.path.join(DATA_DIR, "X_train.csv"))
X_test = pd.read_csv(os.path.join(DATA_DIR, "X_test.csv"))
y_train = pd.read_csv(os.path.join(DATA_DIR, "y_train.csv"))
y_test = pd.read_csv(os.path.join(DATA_DIR, "y_test.csv"))
y_train = np.ravel(y_train)
y_test = np.ravel(y_test)

rf_classifier = ensemble.RandomForestClassifier(n_jobs=-1, random_state=42)

with mlflow.start_run(run_name="Random Forest") as run:
    # Entraînement du modèle
    rf_classifier.fit(X_train, y_train)

    # Évaluation sur les données de test préparées par le preprocess
    y_pred = rf_classifier.predict(X_test)
    accuracy = sklearn.metrics.accuracy_score(y_test, y_pred)
    precision_score = sklearn.metrics.precision_score(
        y_test, y_pred, average="weighted"
    )
    recall_score = sklearn.metrics.recall_score(y_test, y_pred, average="weighted")
    f1_score = sklearn.metrics.f1_score(y_test, y_pred, average="weighted")

    # Enregistrement des métriques dans MLFlow
    mlflow.log_metric("accuracy", accuracy)
    mlflow.log_metric("precision", precision_score)
    mlflow.log_metric("recall", recall_score)
    mlflow.log_metric("f1_score", f1_score)

    # Enregistrement du modèle dans MLFlow
    mlflow.sklearn.log_model(
        rf_classifier,
        artifact_path="random_forest_model",
        registered_model_name="Modèle_Gravité_Accidents",
    )
    print(f"Model logged to MLFlow with run ID: {mlflow.active_run().info.run_id}")
