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
    experiment_id = client.create_experiment(experiment_name)
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
            cursor.execute("SELECT * FROM donnees_accidents WHERE is_ref = 'no';")
            new_data = cursor.fetchall()
            
            print("the data",new_data)

            # Convertir les résultats en DataFrame
            colnames = [desc[0] for desc in cursor.description]
            reference_df = pd.DataFrame(reference_data, columns=colnames)
            new_data_df = pd.DataFrame(new_data, columns=colnames)

            # Définir la colonne num_acc comme index
            reference_df = reference_df.set_index('num_acc')
            new_data_df = new_data_df.set_index('num_acc')

            # Si new_data_df est vide, retourner uniquement reference_df
            if new_data_df.empty:
                return reference_df
            
            # Sinon, concaténer les deux DataFrames
            combined_df = pd.concat([reference_df, new_data_df])

    finally:
        connection.close()
    
    return combined_df

# Fonction pour uploader le model existant en Production aet calculer l'accuracy
def load_production_model_and_evaluate(X_test, y_test, model_name="model_rf_clf"):
    # Récupérer toutes les versions du modèle et chercher le tag "is_production"
    try:
        versions = client.search_model_versions(f"name='{model_name}'")
    except mlflow.exceptions.RestException as e:
        print(f"Model '{model_name}' not found in the registry. No production model to evaluate.")
        return None, None

    prod_model_info = None
    for version in versions:
        if version.tags.get("is_production") == "true":  # Utiliser un tag personnalisé
            prod_model_info = version
            break

    if not prod_model_info:
        print(f"No model tagged as 'is_production=true' exists for '{model_name}'.")
        return None, None
    
    prod_model_version = prod_model_info.version
    print(f"Loading model version {prod_model_version} (tagged as production).")

    model_uri = f"models:/{model_name}/{prod_model_version}"  # Charger une version spécifique
    prod_model = mlflow.pyfunc.load_model(model_uri)
    
    # Faire des prédictions et calculer la précision
    prod_model_predictions = prod_model.predict(X_test)
    prod_model_accuracy = accuracy_score(y_test, prod_model_predictions)
    
    return prod_model_accuracy, prod_model_version


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

    # Evaluer le model de production existant
    prod_model_accuracy, prod_model_version = load_production_model_and_evaluate(X_test, y_test)

    if prod_model_accuracy is not None:
        print(f"Production model accuracy (version {prod_model_version}): {prod_model_accuracy}")
    else:
        print("No production model available for comparison.")
    
    # Démarrer une nouvelle exécution dans l'expérience définie
   
    with mlflow.start_run(run_name=run_name) as run:

        # Enregistrer la précision du nouveau modèle
        mlflow.log_metric("new_model_accuracy", new_model_accuracy)

        # Si un modèle de production existe, enregistrer sa précision
        if prod_model_accuracy is not None:
            mlflow.log_metric("production_model_accuracy", prod_model_accuracy)

        # Enregistrer le nouveau modèle dans MLflow
        mlflow.sklearn.log_model(new_model, model_name)
        model_uri = f"runs:/{run.info.run_id}/{model_name}"
        print(f"New model URI: {model_uri}")

        # Enregistrer le modèle dans le registre de modèles
        mlflow.register_model(model_uri, model_name)
        

        # Récupérer la dernière version du modèle enregistré
        new_version = client.get_latest_versions(model_name)[0].version

        if prod_model_accuracy is None or new_model_accuracy > prod_model_accuracy:
            client.set_model_version_tag(
            name=model_name,
            version=new_version,
            key="is_production",
            value="true"
            )
            print(f"New model version {new_version} promoted to Production.")
        else:
            print(f"New model version {new_version} not promoted as it underperformed compared to the current Production model.")

        



if __name__ == "__main__":
    main()

