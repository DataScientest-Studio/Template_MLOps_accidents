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
mlflow.set_tracking_uri("http://mlflow_service:5000") 
client = MlflowClient()
experiment_name = "accident_prediction"

# voir si experiment existe déja
experiment = client.get_experiment_by_name(experiment_name)

if experiment is None:
    # Créer experiment si n'existe pas
    experiment_id = client.create_experiment(experiment_name,artifact_location="/mlflow/mlruns")
else:
    experiment_id = experiment.experiment_id

print(f"Experiment ID: {experiment_id}")


mlflow.set_experiment(experiment_name)


run_name = "accident_run"
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
            #cursor.execute("SELECT * FROM donnees_accidents WHERE is_ref = 'no';")
            #new_data = cursor.fetchall()

            # Convertir les résultats en DataFrame
            colnames = [desc[0] for desc in cursor.description]
            reference_df = pd.DataFrame(reference_data, columns=colnames)
            #new_data_df = pd.DataFrame(new_data, columns=colnames)

            # Définir la colonne num_acc comme index
            reference_df = reference_df.set_index('num_acc')
            #new_data_df = new_data_df.set_index('num_acc')

            # Concaténer les deux DataFrames
            #combined_df = pd.concat([reference_df, new_data_df])

    finally:
        connection.close()

    return  reference_df


# Fonction pour entraîner un nouveau modèle
def train_new_model(X_train, X_test, y_train, y_test):
    model = RandomForestClassifier(random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    return model, accuracy


# Fonction principale
def main():

    # préparer les  données
    data=load_data_from_db()
    X = data.drop(columns=['grav','timestamp','is_ref'])  
    y = data['grav']

    # Séparer les données en ensemble d'entraînement et de test
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Entraîner le nouveau modèle
    new_model, new_model_accuracy = train_new_model(X_train, X_test, y_train, y_test)
    
    # Démarrer une nouvelle exécution dans l'expérience définie
   
    with mlflow.start_run(run_name=run_name) as run:
        
        mlflow.log_metric("accuracy", new_model_accuracy)
        mlflow.sklearn.log_model(new_model, model_name)
        model_uri = f"runs:/{run.info.run_id}/{model_name}"
        mlflow.register_model(model_uri, model_name)
        new_version = client.get_latest_versions(model_name)[0].version
        client.set_model_version_tag(
            name=model_name,
            version=new_version,
            key="status",
            value="Production"
                )
        print(f"Nouveau modèle enregistré avec le statut 'Production' (version {new_version})")
        
    


if __name__ == "__main__":
    main()

