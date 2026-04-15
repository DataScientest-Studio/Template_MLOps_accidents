import joblib
import pandas as pd
import sys
import json

# Import MLflow utilities for logging metrics
from src.models.mlflow_utils import start_run, log_params, log_metrics, set_tracking_uri

# Load your saved model
loaded_model = joblib.load("./src/models/trained_model.joblib")


def predict_model(features):
    input_df = pd.DataFrame([features])
    print(input_df)
    prediction = loaded_model.predict(input_df)
    return prediction


def get_feature_values_manually(feature_names):
    features = {}
    for feature_name in feature_names:
        feature_value = float(input(f"Enter value for {feature_name}: "))
        features[feature_name] = feature_value
    return features


if __name__ == "__main__":
    if len(sys.argv) == 2:
        json_file = sys.argv[1]
        with open(json_file, "r") as file:
            features = json.load(file)
    else:
        X_train = pd.read_csv("data/preprocessed/X_train.csv")
        feature_names = X_train.columns.tolist()
        features = get_feature_values_manually(feature_names)

    #======================================================================
    # - MLflow considère le inputs comme des paramètres
    # - et les résultats comme des métriques.
    #=====================================================================
    # On configure le tracking URI pour MLflow
    set_tracking_uri("http://localhost:5000")
    
    # Démarrage d'un run MLflow pour la prédiction
    with start_run(run_name="Prediction_Run") as run:
        
        # log des features (input)
        log_params(features)

        result = predict_model(features)

        # log de la prédiction (output)
        log_metrics({"prediction": int(result[0])})

    print(f"prediction : {result[0]}")
