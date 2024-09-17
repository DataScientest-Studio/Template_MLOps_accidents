import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import pandas as pd
from mlflow.tracking import MlflowClient
import psycopg2
from psycopg2 import sql
import os

# Configuration MLflow
mlflow.set_tracking_uri("http://mlflow-server:5000")
mlflow.set_experiment("retraining_experiment")

client = MlflowClient()
model_name = "model_rf_clf"

# Fonction pour obtenir une connexion à la database
def get_db_connection():
    connection = psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB", "accidents"),
        user=os.getenv("POSTGRES_USER", "my_user"),
        password=os.getenv("POSTGRES_PASSWORD", "your_password"),
        host=os.getenv("POSTGRES_HOST", "db"),  
        port=os.getenv("POSTGRES_PORT", "5432")
    )
    return connection

# Fonction pour charger les données depuis la database
def load_data_from_db():
    """
    Charger les données de la table 'donnees_accidents' à partir de la base de données PostgreSQL.
    """
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Charger les données de référence
            cursor.execute("SELECT * FROM donnees_accidents WHERE is_ref = 'yes';")
            reference_data = cursor.fetchall()

            # Charger les nouvelles données
            cursor.execute("SELECT * FROM donnees_accidents WHERE is_ref = 'no';")
            new_data = cursor.fetchall()

            # Convertir les résultats en DataFrame
            colnames = [desc[0] for desc in cursor.description]
            reference_df = pd.DataFrame(reference_data, columns=colnames)
            new_data_df = pd.DataFrame(new_data, columns=colnames)

            # Définir la colonne num_acc comme index
            reference_df = reference_df.set_index('num_acc')
            new_data_df = new_data_df.set_index('num_acc')

            # Concaténer les deux DataFrames
            combined_df = pd.concat([reference_df, new_data_df])

    finally:
        connection.close()

    return combined_df


# Fonction pour entraîner un nouveau modèle
def train_new_model(X_train, X_test, y_train, y_test):
    model = RandomForestClassifier(random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    return model, accuracy

# Fonction pour charger le modèle en production
def load_production_model(model_name):
    versions = client.get_latest_versions(model_name, stages=["Production"])
    if len(versions) == 0:
        print("Aucun modèle en production trouvé.")
        return None
    production_version = versions[0]
    model_uri = f"models:/{model_name}/Production"
    production_model = mlflow.sklearn.load_model(model_uri)
    return production_model


# Fonction pour comparer les modèles
def compare_models(new_model_accuracy, production_model,X_test, y_test ):
    prod_y_pred = production_model.predict(X_test)
    production_model_accuracy = accuracy_score(y_test, prod_y_pred)
    print(f"Performance du nouveau modèle : {new_model_accuracy}")
    print(f"Performance du modèle en production : {production_model_accuracy}")
    return production_model_accuracy

# Fonction pour enregistrer le modèle avec MLflow
def log_model(model, accuracy):
    with mlflow.start_run() as run:
        mlflow.log_metric("accuracy", accuracy)
        mlflow.sklearn.log_model(model, "model_rf_clf")
        model_uri = f"runs:/{run.info.run_id}/model_rf_clf"
        mlflow.register_model(model_uri, model_name)
        return run.info.run_id
    
# Fonction pour promouvoir un modèle en production
def promote_model(run_id):
    model_uri = f"runs:/{run_id}/model_rf_clf"
    mlflow.register_model(model_uri, model_name)
    new_version = client.get_latest_versions(model_name)[0].version
    client.transition_model_version_stage(
        name=model_name,
        version=new_version,
        stage="Production"
    )
    print(f"Nouveau modèle promu en Production (version {new_version})")

# Fonction principale
def main():

    # préparer les  données
    data=load_data_from_db()
    X = data.drop(columns=['grav'])  
    y = data['grav']

    # Séparer les données en ensemble d'entraînement et de test
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Entraîner le nouveau modèle
    new_model, new_model_accuracy = train_new_model(X_train, X_test, y_train, y_test)
    
    # Charger le modèle en production
    production_model = load_production_model(model_name)
    
    if production_model:
        # Comparer les modèles
        production_model_accuracy = compare_models(new_model_accuracy, production_model, X_test, y_test)
        
        # Promouvoir le nouveau modèle si nécessaire
        if new_model_accuracy > production_model_accuracy:
            run_id = log_model(new_model, new_model_accuracy)
            promote_model(run_id)
        else:
            print("Le modèle en production est meilleur. Pas de changement.")
    else:
        # Pas de modèle en production, promouvoir directement
        run_id = log_model(new_model, new_model_accuracy)
        promote_model(run_id)




