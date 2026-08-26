import streamlit as st

st.set_page_config(page_title="Accident Classifier", layout="wide")

pages = [
    st.Page("views/01_accueil_architecture.py", title="Accueil", default=True),
    st.Page("views/03_github_page.py", title="CI/CD & GitHub Projects"),
    st.Page("views/04_docker_page.py", title="Docker"),
    st.Page("views/06_airflow_page.py", title="Airflow - Orchestration"),
    st.Page("views/02_donnees_preprocessing.py", title="Données & préprocessing"),
    st.Page("views/05_mlflow_page.py", title="MLflow / Entraînement"),
    st.Page("views/07_bentoml_page.py", title="BentoML"),
    st.Page("views/08_nginx_page.py", title="Nginx"),
    st.Page("views/09_prometheus_page.py", title="Prometheus"),
    st.Page("views/10_grafana_page.py", title="Grafana"),
    st.Page("views/11_data_drift_page.py", title="Data drift"),
    st.Page("views/12_prediction_page.py", title="App de Prédiction"),
]

pg = st.navigation(pages)
pg.run()
