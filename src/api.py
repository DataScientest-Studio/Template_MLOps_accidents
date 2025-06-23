import joblib
from fastapi import FastAPI
import os

app = FastAPI()

# Chemin vers le modèle pré-entraîné
model_path = os.path.join(os.path.dirname(__file__), 'models', 'trained_model.joblib')

model = joblib.load(model_path)

@app.get("/")
def read_root():
    return {"message": "Model loaded successfully"}
