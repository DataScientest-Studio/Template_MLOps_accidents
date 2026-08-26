import streamlit as st

st.set_page_config(
    page_title="MLOps Accidents - Airflow - Orchestration",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .main-header {font-size: 2.8rem; font-weight: bold; color: #1f77b4; margin-bottom: 0.75rem;}
    .sub-header {font-size: 1.5rem; font-weight: 600; color: #333; margin-top: 1.75rem;}
    .info-box {background-color: #fff4e5; border-left: 5px solid #e69138; padding: 1rem; border-radius: 8px; margin: 1rem 0;}
    .code-box {background-color: #f7f7f7; padding: 1rem; border-radius: 8px; border: 1px solid #e0e0e0;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<p class="main-header">Airflow : orchestration du pipeline MLOps</p>', unsafe_allow_html=True)
st.markdown(
    "Airflow orchestre l'ensemble du pipeline de bout en bout : préparation des données, entraînement, évaluation, promotion du modèle et rechargement du service de prédiction."
)

st.markdown(
    "<div style='text-align:center; margin: 1rem 0;'>"
    "<a href='http://localhost:8080' target='_blank'>"
    "<button style='background-color:#28a745; color:white; border:none; padding:15px 30px; font-size:1.2rem; border-radius:5px; cursor:pointer;'>"
    "Ouvrir Airflow UI</button></a>"
    "</div>",
    unsafe_allow_html=True,
)

st.divider()

st.markdown('<p class="sub-header">1. DAG principal : <code>mlops_accident_gravity_pipeline</code></p>', unsafe_allow_html=True)
st.markdown(
    """
    Le DAG `mlops_accident_gravity_pipeline` est défini dans `dags/pipeline_accidents.py`.
    Il s'exécute **mensuellement** et est conçu pour être robuste : `catchup=False`, reruns contrôlés, et relance du modèle seulement si la qualité est conservée.
    """
)

st.markdown("### Étapes du pipeline")
col1, col2 = st.columns([1, 1])
with col1:
    st.markdown("**1. preprocess**")
    st.write("DockerOperator exécute le container `mlops_accidents-preprocess:latest` et alimente le volume `accidents-data`.")
    st.markdown("**2. train**")
    st.write("DockerOperator exécute `mlops_accidents-train:latest` et envoie ses métriques vers MLflow.")
with col2:
    st.markdown("**3. evaluate_metrics**")
    st.write("PythonOperator vérifie le dernier run MLflow et compare le nouveau modèle au champion.")
    st.markdown("**4. promote_model / reload_predict_service**")
    st.write("Si le nouveau modèle est au moins aussi bon, il est promu en `@champion` et BentoML est invité à recharger le modèle.")

st.markdown("### Pourquoi Airflow ici ?")
st.info(
    "Airflow sépare la logique métier des exécutions : chaque tâche est isolée, les dépendances sont explicites et les erreurs sont localisées. "
    "Cela facilite aussi le débogage et le rerun d'une étape sans tout relancer."
)

st.markdown('<p class="sub-header">2. Intégration MLflow & BentoML</p>', unsafe_allow_html=True)
st.markdown(
    """
    - Le `train` monte le volume `accidents-data` et reçoit `MLFLOW_TRACKING_URI` en variable d'environnement.
    - `evaluate_metrics` lit le dernier run MLflow et compare le modèle `runs:/{run_id}/random_forest_model` avec le modèle champion `models:/Modèle_Gravité_Accidents@champion`.
    - `reload_predict_service` appelle l'endpoint interne `/reload_model` de `ml-api`.
    """
)

st.markdown("### Ligne de code clé")
st.code(
    """
with DAG(
    'mlops_accident_gravity_pipeline',
    default_args=default_args,
    schedule='@monthly',
    catchup=False,
) as dag:
    task_preprocess = DockerOperator(...)
    task_train = DockerOperator(...)
    task_evaluate = PythonOperator(...)
    task_promote = PythonOperator(...)
    task_reload = PythonOperator(...)
    task_preprocess >> task_train >> task_evaluate
    task_evaluate >> task_promote
    task_evaluate >> task_reload
    """,
    language="python",
)

st.divider()

st.markdown('<p class="sub-header">3. Valeur apportée</p>', unsafe_allow_html=True)
st.markdown(
    """
    - Orchestration automatisée des cycles de reprise.
    - Contrôle qualité avant promotion du modèle.
    - Migration du modèle en production sans downtime grâce au rechargement BentoML.
    - Transparence totale sur les exécutions et les erreurs via l'UI Airflow.
    """
)

st.success(
    "Airflow n'est pas qu'un scheduler : c'est le garant que la chaîne ML se déroule dans le bon ordre, avec des validations automatiques à chaque étape."
)
