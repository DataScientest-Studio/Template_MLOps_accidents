import sys
import argparse
from pathlib import Path
import pandas as pd
from sklearn import ensemble
import joblib
import numpy as np
import mlflow

# Import des fonctions utilitaires pour MLflow
from src.models.mlflow_utils import set_tracking_uri, set_experiment, start_run, log_params, log_model

# 1. Gestion propre des arguments avec argparse
parser = argparse.ArgumentParser()
parser.add_argument("--train_path", type=str, default="data/preprocessed", help="Dossier contenant les CSV")
parser.add_argument("--model_output", type=str, default="models/model.joblib", help="Fichier de sortie du modèle")
args = parser.parse_args()

input_filepath = Path(args.train_path)
output_model_path_filename = Path(args.model_output)

# 2. Vérification du chemin d'entrée
if not input_filepath.exists():
    print(f"❌ Erreur : Le chemin '{input_filepath}' n'existe pas !")
    print(f"📍 Emplacement actuel : {Path.cwd()}")
    sys.exit(1)

# Sécurité : Création du dossier parent pour le modèle
output_model_path_filename.parent.mkdir(parents=True, exist_ok=True)

print(f"✅ Source path checked : {input_filepath}")

# 3. Chargement des données
# Note : On utilise le dossier fourni pour charger les 4 fichiers
X_train = pd.read_csv(input_filepath / "X_train.csv")
X_test = pd.read_csv(input_filepath / "X_test.csv")
y_train = pd.read_csv(input_filepath / "y_train.csv")
y_test = pd.read_csv(input_filepath / "y_test.csv")

y_train = np.ravel(y_train)
y_test = np.ravel(y_test)

# 4. Configuration MLflow
rf_classifier = ensemble.RandomForestClassifier(n_jobs=-1)

# Note : Si vous utilisez DagsHub, l'URI sera différent de localhost
# Mais on laisse l'orchestrateur gérer l'expérience
set_tracking_uri("http://localhost:5000") 
#set_experiment("01_Gravity_Accident")

# Récupération du run actif (créé par la commande terminale :"mlflow run .") si elle existe, 
# sinon création d'un nouveau run avec cette instruction : start_run()
active_run = mlflow.active_run()   
run_id = active_run.info.run_id if active_run else None

# Si run_id existe, on reprend le run de l'orchestrateur.
# On active nested=True pour éviter tout conflit de hiérarchie
with start_run(run_name="RandomForest_v1", run_id=run_id, nested=True):
    log_params({"n_jobs": -1, "model_type": "RandomForest"})
    
    rf_classifier.fit(X_train, y_train)
    
    # Log du modèle dans MLflow
    log_model(rf_classifier)

# 5. Sauvegarde physique du modèle (pour DVC)
joblib.dump(rf_classifier, output_model_path_filename)
print(f"✅ Model trained and saved successfully here : {output_model_path_filename}")