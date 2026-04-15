import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier

# chemins
BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(exist_ok=True)

MODEL_PATH = MODEL_DIR / "model.joblib"
FEATURES_PATH = BASE_DIR / "src" / "models" / "test_features.json"

# charger les features attendues par l'API
with open(FEATURES_PATH, "r", encoding="utf-8") as f:
    sample = json.load(f)

feature_names = list(sample.keys())

# créer un petit dataset synthétique compatible
rows = []
targets = []

base = sample.copy()

for i in range(200):
    row = {}
    for k, v in base.items():
        if isinstance(v, (int, float)):
            noise = np.random.normal(0, 1)
            row[k] = float(v) + noise
        else:
            row[k] = v
    rows.append(row)

    # cible binaire simple pour démo / monitoring
    targets.append(np.random.randint(0, 2))

X = pd.DataFrame(rows, columns=feature_names)
y = np.array(targets)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

joblib.dump(model, MODEL_PATH)

print(f"Modèle compatible API sauvegardé dans : {MODEL_PATH}")
print("Colonnes utilisées :", X.columns.tolist())
print("Shape :", X.shape)