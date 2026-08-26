from datetime import datetime
from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.operators.python import PythonOperator
from airflow.exceptions import AirflowFailException
from docker.types import Mount
import mlflow
import pandas as pd
from airflow.utils.trigger_rule import TriggerRule
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from mlflow.tracking import MlflowClient
import requests
import os
from sklearn.metrics import f1_score


DATA_VOLUME_NAME = os.getenv("DATA_VOLUME_NAME", "mlops_accidents_accidents-data")
MLFLOW_TRACKING_URI = "http://mlflow:5000"
EXPERIMENT_NAME = "Gravité_Accidents"
MODEL_NAME = "Modèle_Gravité_Accidents"
DOCKER_NETWORK = "mlops_accidents_default"
VALIDATION_DATA_DIR = "/opt/airflow/data/preprocessed"


default_args = {
    "owner": "mlops_team",
    "start_date": datetime(2026, 1, 1),
    "retries": 1,
}


def check_metrics_and_alert(**context):
    """
    Évalue le nouveau modèle et le champion sur le même jeu de validation,
    puis décide si le nouveau modèle doit être promu.
    """
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    client = MlflowClient()

    experiment = client.get_experiment_by_name(EXPERIMENT_NAME)
    if not experiment:
        raise AirflowFailException(
            f"L'expérience '{EXPERIMENT_NAME}' n'a pas été trouvée dans MLflow."
        )

    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=["attributes.start_time DESC"],
        max_results=1,
    )

    if not runs:
        raise AirflowFailException(
            f"Aucun run trouvé pour l'expérience {EXPERIMENT_NAME}."
        )

    current_run = runs[0]
    current_run_id = current_run.info.run_id
    current_f1 = current_run.data.metrics.get("f1_score")

    should_promote = True

    context["ti"].xcom_push(key="current_run_id", value=current_run_id)
    print(
        f"Nouveau modèle entraîné détecté - Run ID: {current_run_id} | F1-Score du run: {current_f1}"
    )

    if current_f1 is None:
        raise AirflowFailException(
            "Le dernier run MLflow n'a pas enregistré de métrique 'f1_score'."
        )

    validation_features_path = os.path.join(VALIDATION_DATA_DIR, "X_test.csv")
    validation_target_path = os.path.join(VALIDATION_DATA_DIR, "y_test.csv")

    if not os.path.exists(validation_features_path) or not os.path.exists(
        validation_target_path
    ):
        raise AirflowFailException(
            f"Fichiers de validation introuvables dans {VALIDATION_DATA_DIR}."
        )

    X_val = pd.read_csv(validation_features_path)
    y_val = pd.read_csv(validation_target_path).values.ravel()

    try:
        prod_model_version = client.get_model_version_by_alias(MODEL_NAME, "champion")
        champion_model_uri = f"models:/{MODEL_NAME}@champion"
        champion_model = mlflow.sklearn.load_model(champion_model_uri)
        champion_pred = champion_model.predict(X_val)
        champion_f1 = f1_score(y_val, champion_pred, average="weighted")

        new_model = mlflow.sklearn.load_model(
            f"runs:/{current_run_id}/random_forest_model"
        )
        new_pred = new_model.predict(X_val)
        new_f1 = f1_score(y_val, new_pred, average="weighted")

        print(
            f"Comparaison sur le même jeu de validation : "
            f"Champion F1 = {champion_f1:.3f} | Nouveau F1 = {new_f1:.3f}"
        )

        if new_f1 < champion_f1:
            should_promote = False
            print(
                "Le nouveau modèle est strictement moins bon que le champion sur les mêmes données de validation."
            )
        else:
            print(
                "Le nouveau modèle a un F1 score au moins égal à celui du champion sur les mêmes données de validation."
            )
    except mlflow.exceptions.MlflowException as exc:
        print(
            f"Aucun modèle marqué '@champion' trouvé. Première promotion du projet. ({exc})"
        )

    context["ti"].xcom_push(key="should_promote", value=should_promote)


def promote_model_to_champion(**context):
    """
    Associe l'alias 'champion' à la dernière version du modèle validé
    seulement si le nouveau modèle est meilleur que le champion.
    """
    should_promote = context["ti"].xcom_pull(
        key="should_promote", task_ids="evaluate_metrics"
    )
    if should_promote is False:
        print(
            "Le modèle champion reste inchangé, car le nouveau modèle n'est pas meilleur."
        )
        return

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    client = MlflowClient()

    run_id = context["ti"].xcom_pull(key="current_run_id", task_ids="evaluate_metrics")

    filter_string = f"run_id='{run_id}'"
    versions = client.search_model_versions(filter_string)

    if not versions:
        raise AirflowFailException(
            f"Aucune version de modèle trouvée dans le Registry pour le run {run_id}."
        )

    latest_version = versions[0].version

    client.set_registered_model_alias(MODEL_NAME, "champion", latest_version)
    print(
        f"Succès : Le modèle '{MODEL_NAME}' version {latest_version} est maintenant désigné comme '@champion'."
    )


def reload_predict_service():
    """
    Déclenche un appel vers le conteneur d'API (ml-api) pour recharger
    en mémoire la version associée à l'alias '@champion'.
    """
    bento_url = "http://ml-api:3000/reload_model"
    try:
        response = requests.post(bento_url, timeout=15)
        response.raise_for_status()
        print("Le conteneur 'ml-api' a mis à jour son modèle avec succès.")
    except Exception as e:
        raise AirflowFailException(f"Échec du rechargement de ml-api : {e}")


with DAG(
    "mlops_accident_gravity_pipeline",
    default_args=default_args,
    description="Pipeline d'entraînement pour la gravité des accidents",
    schedule="@monthly",
    catchup=False,
    is_paused_upon_creation=False,
    tags=["accidents"],
) as dag:
    task_preprocess = DockerOperator(
        task_id="preprocess",
        image="mlops_accidents-preprocess:latest",
        api_version="auto",
        auto_remove=True,
        mount_tmp_dir=False,
        network_mode=DOCKER_NETWORK,
        mounts=[Mount(source=f"{DATA_VOLUME_NAME}", target="/app/data", type="volume")],
    )

    task_train = DockerOperator(
        task_id="train",
        image="mlops_accidents-train:latest",
        api_version="auto",
        auto_remove=True,
        mount_tmp_dir=False,
        network_mode=DOCKER_NETWORK,
        environment={"MLFLOW_TRACKING_URI": MLFLOW_TRACKING_URI},
        mounts=[Mount(source=f"{DATA_VOLUME_NAME}", target="/app/data", type="volume")],
    )

    task_evaluate = PythonOperator(
        task_id="evaluate_metrics",
        python_callable=check_metrics_and_alert,
    )

    task_promote = PythonOperator(
        task_id="promote_model",
        python_callable=promote_model_to_champion,
    )

    task_reload = PythonOperator(
        task_id="reload_predict_service",
        python_callable=reload_predict_service,
        trigger_rule=TriggerRule.ALL_DONE,
    )

    task_trigger_drift = TriggerDagRunOperator(
        task_id="trigger_drift_monitoring",
        trigger_dag_id="drift_monitoring",
        wait_for_completion=False,
        trigger_rule=TriggerRule.ALL_DONE,
    )

    task_preprocess >> task_train >> task_evaluate
    task_evaluate >> task_promote
    task_evaluate >> task_reload
    [task_promote, task_reload] >> task_trigger_drift
