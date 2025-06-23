import os
import json
import joblib
import pandas as pd
import numpy as np
from src.models import train_model  
from src.models import predict_model

def test_train_and_save_model():
    # Charger les données prétraitées 
    X_train = pd.read_csv('data/preprocessed/X_train.csv').head(50)
    y_train = pd.read_csv('data/preprocessed/y_train.csv').head(50)
    y_train = np.ravel(y_train)

    from sklearn.ensemble import RandomForestClassifier
    rf = RandomForestClassifier(n_jobs=-1)

    rf.fit(X_train, y_train)

    model_path = './src/models/trained_model_test.joblib'
    joblib.dump(rf, model_path)

    assert os.path.exists(model_path)

    # Nettoyage
    os.remove(model_path)

def test_prediction_with_sample_features():
    # Charger le modèle déjà entraîné
    model_path = './src/models/trained_model.joblib'
    model = joblib.load(model_path)

    features = {
        "place": 10,
        "catu": 3,
        "sexe": 1,
        "secu1": 0.0,
        "year_acc": 2021,
        "victim_age": 60,
        "catv": 2,
        "obsm": 1,
        "motor": 1,
        "catr": 3,
        "circ": 2,
        "surf": 1,
        "situ": 1,
        "vma": 50,
        "jour": 7,
        "mois": 12,
        "lum": 5,
        "dep": 77,
        "com": 77317,
        "agg_": 2,
        "int": 1,
        "atm": 0,
        "col": 6,
        "lat": 48.60,
        "long": 2.89,
        "hour": 17,
        "nb_victim": 2,
        "nb_vehicules": 1
    }

    input_df = pd.DataFrame([features])
    prediction = model.predict(input_df)

    assert prediction.shape[0] == 1
    assert prediction[0] in [0, 1]  

if __name__ == "__main__":
    test_train_and_save_model()
    test_prediction_with_sample_features()
    print("Tous les tests passent !") 
