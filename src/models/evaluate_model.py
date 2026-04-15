# evaluate_model.py (version ed01) dans src/models/

import pandas as pd
import joblib
import json
import sys
from pathlib import Path
from sklearn.metrics import accuracy_score, classification_report, f1_score

# Import MLflow utilities for logging metrics
from src.models.mlflow_utils import log_metrics, set_tracking_uri, set_experiment, start_run

def evaluate(model_file_path, data_path, metrics_file_path):
    # 1. Chargement du modèle
    print(f"Chargement du modèle : {model_file_path}")
    model = joblib.load(model_file_path)

    # 2. Chargement des données de test
    X_test = pd.read_csv(data_path / "X_test.csv")
    y_test = pd.read_csv(data_path / "y_test.csv")

    # 3. Prédictions
    print("Évaluation en cours...")
    y_pred = model.predict(X_test)

    # 4. Calcul des métriques
    report = classification_report(y_test, y_pred, output_dict=True)
    # KPIs précision, recall, f1 pour la classe 0 (bénin)
    class_0 = report.get("0", report.get(0, {}))
    # KPIs précision, recall, f1 pour la classe 1 (grave)
    class_1 = report.get("1", report.get(1, {}))

    metrics = {
        "global": {
            "accuracy": accuracy_score(y_test, y_pred),
            # moyenne arithmétique (average="macro") de f1 bénin et f1 grave
            # NB: la moyenne harmonique pénaliserait trop la valeur de f1
            "f1_macro_avg": f1_score(y_test, y_pred, average="macro"),
        },
        "classe_0_benin": {
            "precision": class_0.get("precision", 0),
            "recall": class_0.get("recall", 0),
            "f1-score": class_0.get("f1-score", 0),
        },
        "classe_1_grave": {
            "precision": class_1.get("precision", 0),
            "recall": class_1.get("recall", 0),
            "f1-score": class_1.get("f1-score", 0), 
        },
    }

    #=====================================================================
    # Obtention d'un dictionnaire de métriques "aplati" pour MLflow
    #=====================================================================
    # Utilisation de MLflow pour le suivi des métriques
    set_tracking_uri("http://localhost:5000") 

    set_experiment("01_Gravity_Accident")

    #--- MLflow logging ---
    flat_metrics = {
        "accuracy": metrics["global"]["accuracy"] ,
        "f1_macro_avg": metrics["global"]["f1_macro_avg"],
    
        "precision_classe_0": metrics["classe_0_benin"]["precision"],
        "recall_classe_0": metrics["classe_0_benin"]["recall"],
        "f1_classe_0": metrics["classe_0_benin"]["f1-score"],

        "precision_classe_1": metrics["classe_1_grave"]["precision"],
        "recall_classe_1": metrics["classe_1_grave"]["recall"],
        "f1_classe_1": metrics["classe_1_grave"]["f1-score"],
    }

    # Enregistrement des métriques dans MLflow
    with start_run(run_name="Evaluation_v1") as run:
        log_metrics(flat_metrics)

    # 5. Sauvegarde des métriques en JSON
    with open(metrics_file_path, "w") as f:
        json.dump(metrics, f, indent=4)

    print(f"✅ Rapport terminé : {metrics_file_path}")

    # --- Affichage sur la console ---
    print("\n" + "=" * 40)
    print("📊 RÉSULTATS DE L'ÉVALUATION")
    print("=" * 40)
    print(f"🎯Précision Globale (accuracy): {metrics['global']['accuracy']:.2%}")
    print(f"⚖️Équilibre (F1 Macro Avg)    : {metrics['global']['f1_macro_avg']:.4f}")
    print("-" * 40)
    print("🚨 CLASSE 1 (GRAVE) :")
    print(f"   ↳ Précision (precision) : {metrics['classe_1_grave']['precision']:.2%}")
    print(f"   ↳ Rappel (recall)       : {metrics['classe_1_grave']['recall']:.2%}")
    print(f"   ↳ F1-Score              : {metrics['classe_1_grave']['f1-score']:.4f}")
    print("-" * 40)
    print("🛡️ CLASSE 0 (BENIN) :")
    print(f"   ↳ Précision (precision) : {metrics['classe_0_benin']['precision']:.2%}")
    print(f"   ↳ Rappel (recall)       : {metrics['classe_0_benin']['recall']:.2%}")
    print(f"   ↳ F1-Score              : {metrics['classe_0_benin']['f1-score']:.4f}")
    print("=" * 40 + "\n")


if __name__ == "__main__":

    # Récupération des arguments de la ligne de commande
    # Crash ici si le dvc.yaml est incomplet
    try:
        model_file_path = Path(sys.argv[1])
        data_path = Path(sys.argv[2])
        metrics_file_path = Path(sys.argv[3])
    except IndexError:
        print("❌ Erreur : dvc.yaml n'a pas fourni assez d'arguments.")
        sys.exit(1)

    # On vérifie si les chemin d'entrée EXISTE vraiment
    if not model_file_path.exists():
        print(
            "❌ Erreur de syntaxe dans dvc.yaml : "
            f"Le chemin '{model_file_path}' n'existe pas !"
        )
        print(f"📍 Emplacement actuel : {Path.cwd()}")
        sys.exit(1)

    if not data_path.exists():
        print(
            "❌ Erreur de syntaxe dans dvc.yaml : "
            f"Le chemin '{data_path}' n'existe pas !"
        )
        print(f"📍 Emplacement actuel : {Path.cwd()}")
        sys.exit(1)

    evaluate(model_file_path, data_path, metrics_file_path)
