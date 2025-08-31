import datetime
import requests
import pendulum
import joblib
import os
import pandas as pd
import pickle
import subprocess
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sdk import dag, task


@dag(
    dag_id="process_accidents_prediction",
    schedule="0 0 * * *",
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    catchup=False,
    dagrun_timeout=datetime.timedelta(minutes=60),
)

# @task
# def loadModel_from_DVC():
#     try:
#         model_path = "/opt/airflow/dags/models/trained_model.joblib"

#         with open(model_path, 'rb') as f:
#             loaded_model = joblib.load(f)

#     except Exception as e:
#             print(f"Error loading model from DVC: {str(e)}")
#             raise

def ProcessAccidentModel():
    @task
    def get_data():
        base_url = "https://dagshub.com/CarolinHertel/MLOps_accidents/raw/42fd24da8e1e1d64683417aa1da5bd035bbdb7c6/data/preprocessed/"
        files = {
            "X_train.csv": "/opt/airflow/dags/files/X_train.csv",
            "X_test.csv": "/opt/airflow/dags/files/X_test.csv",
            "y_train.csv": "/opt/airflow/dags/files/y_train.csv",
            "y_test.csv": "/opt/airflow/dags/files/y_test.csv"
        }
        for filename, local_path in files.items():
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            url = base_url + filename
            print(f"Downloading {filename} from {url}...")
            r = requests.get(url)
            r.raise_for_status()
            with open(local_path, "wb") as f:
                f.write(r.content)
        print("Alle Dateien erfolgreich heruntergeladen!")
        return {
            "X_train_path": files["X_train.csv"],
            "X_test_path": files["X_test.csv"],
            "y_train_path": files["y_train.csv"],
            "y_test_path": files["y_test.csv"]
        }

    @task
    def train_model(data_paths):
        try:
            # Lade die Trainingsdaten
            X_train = pd.read_csv(data_paths["X_train_path"])
            y_train = pd.read_csv(data_paths["y_train_path"])
            
            # Falls y_train mehrere Spalten hat, nehme nur die erste
            if y_train.shape[1] > 1:
                y_train = y_train.iloc[:, 0]
            else:
                y_train = y_train.values.ravel()
            
            # Initialisiere Random Forest Classifier
            rf_classifier = RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                n_jobs=-1  # Nutze alle verfügbaren CPU-Kerne
            )
            
            # Trainiere das Modell
            print("Starte Model Training...")
            rf_classifier.fit(X_train, y_train)
            print("Model Training abgeschlossen!")
            
            # Speichere das trainierte Modell
            model_path = "/opt/airflow/dags/models/rf_classifier_model.pkl"
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            
            with open(model_path, 'wb') as f:
                pickle.dump(rf_classifier, f)
            
            print(f"Modell gespeichert unter: {model_path}")
            
            return {
                "model_path": model_path,
                "feature_importance": rf_classifier.feature_importances_.tolist(),
                "n_features": X_train.shape[1],
                "n_samples": X_train.shape[0]
            }
            
        except Exception as e:
            print(f"Fehler beim Training: {str(e)}")
            raise

    @task
    def evaluate_model(model_info, data_paths):
        """
        Evaluiert das trainierte Modell auf den Testdaten
        """
        try:
            # Lade das trainierte Modell
            with open(model_info["model_path"], 'rb') as f:
                rf_classifier = pickle.load(f)
            
            # Lade die Testdaten
            X_test = pd.read_csv(data_paths["X_test_path"])
            y_test = pd.read_csv(data_paths["y_test_path"])
            
            # Falls y_test mehrere Spalten hat, nehme nur die erste
            if y_test.shape[1] > 1:
                y_test = y_test.iloc[:, 0]
            else:
                y_test = y_test.values.ravel()
            
            # Mache Vorhersagen
            y_pred = rf_classifier.predict(X_test)
            
            # Berechne Metriken
            accuracy = accuracy_score(y_test, y_pred)
            
            # Erstelle Evaluation Report
            evaluation_results = {
                "accuracy": accuracy,
                "classification_report": classification_report(y_test, y_pred, output_dict=True),
                "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
                "test_samples": len(y_test)
            }
            
            print(f"Model Accuracy: {accuracy:.4f}")
            print("Classification Report:")
            print(classification_report(y_test, y_pred))
            
            # Speichere Evaluationsergebnisse
            results_path = "/opt/airflow/dags/results/evaluation_results.pkl"
            os.makedirs(os.path.dirname(results_path), exist_ok=True)
            
            with open(results_path, 'wb') as f:
                pickle.dump(evaluation_results, f)
            
            print(f"Evaluationsergebnisse gespeichert unter: {results_path}")
            
            return evaluation_results
            
        except Exception as e:
            print(f"Fehler bei der Evaluation: {str(e)}")
            raise
    
    @task
    def log_model_info(model_info, evaluation_results):
        print("=== MODEL TRAINING SUMMARY ===")
        print(f"Modell saved under: {model_info['model_path']}")
        print(f"Number Features: {model_info['n_features']}")
        print(f"Number Samples: {model_info['n_samples']}")
        print(f"Test Accuracy: {evaluation_results['accuracy']:.4f}")
        print(f"Number Testsamples: {evaluation_results['test_samples']}")
        
        # Zeige die wichtigsten Features
        if model_info['feature_importance']:
            print("\nTop 5 wichtigste Features:")
            feature_importance = model_info['feature_importance']
            top_features = sorted(enumerate(feature_importance), key=lambda x: x[1], reverse=True)[:5]
            for idx, importance in top_features:
                print(f"  Feature {idx}: {importance:.4f}")
        
        print("=== END SUMMARY ===")
        
        return "Model training pipeline completed successfully!"

    # Definiere die Task-Abhängigkeiten
    data_paths = get_data()
    model_info = train_model(data_paths)
    evaluation_results = evaluate_model(model_info, data_paths)
    final_log = log_model_info(model_info, evaluation_results)

dag = ProcessAccidentModel()