# V2
import joblib
import pandas as pd
from fastapi import FastAPI, Request
import os

BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "trained_model.joblib")

# Load your saved model
loaded_model = joblib.load(MODEL_PATH)

app = FastAPI()

@app.post("/predict")
async def prediction(request: Request):
    data_dict = await request.json()
    df = pd.DataFrame([data_dict])
    pred = loaded_model.predict(df)
    return {"prediction": pred.tolist()}

# V1
"""import joblib 
import pandas as pd
import sys
import json

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
        with open(json_file, 'r') as file:
            features = json.load(file)
    else:
        X_train = pd.read_csv("data/preprocessed/X_train.csv")
        feature_names = X_train.columns.tolist()
        features = get_feature_values_manually(feature_names)

    result = predict_model(features)
    print(f"prediction : {result[0]}") # ici faut qu'on arrive à transmettre le résultat au container streamlit
"""