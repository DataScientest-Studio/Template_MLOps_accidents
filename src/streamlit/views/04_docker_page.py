import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Docker - Infrastructure",
    page_icon="🐳",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .main-header {font-size: 2.8rem; font-weight: bold; color: #0db7ed; margin-bottom: 0.75rem;}
    .sub-header {font-size: 1.5rem; font-weight: 600; color: #333; margin-top: 1.75rem;}
    .service-card {background-color: #f0f8ff; border-left: 5px solid #0db7ed; padding: 1rem; border-radius: 8px; margin: 0.5rem 0;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<p class="main-header">Docker : infrastructure du projet</p>', unsafe_allow_html=True)
st.markdown(
    "L'ensemble du projet tourne dans des **conteneurs Docker** orchestrés via **Docker Compose**. "
    "Chaque service est isolé, reproductible et peut être lancé d'une seule commande : `docker compose up`."
)

st.divider()

st.markdown('<p class="sub-header">1. Architecture globale</p>', unsafe_allow_html=True)
st.markdown(
    "Le projet compte **13 services** répartis en 4 couches fonctionnelles. "
    "Le schéma ci-dessous montre comment ils communiquent entre eux."
)

components.html(
    """
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>mermaid.initialize({startOnLoad: true, theme: 'default'});</script>
    <div class="mermaid">
    flowchart TD
      subgraph Orchestration
        P1[postgres-airflow]
        P2[airflow-init]
        P3[airflow]
      end

      subgraph Tracking_Registre
        MLF[mlflow]
      end

      subgraph Modélisation
        PRE[preprocess]
        TRN[train]
      end

      subgraph API_Serving
        API[ml-api / BentoML]
      end

      subgraph Monitoring_Front
        PROM[prometheus]
        GRAF[grafana]
        STRM[streamlit]
        NGINX[nginx]
      end

      P3 -->|schedule| PRE
      P3 -->|schedule| TRN
      PRE -->|data volume| TRN
      TRN -->|metrics + model| MLF
      MLF -->|champion alias| API
      P3 -->|reload_model| API
      API -->|metrics| PROM
      STRM -->|api requests| API
      NGINX -->|proxy| STRM
      NGINX -->|proxy /predict| API
      PROM -->|datasource| GRAF
      MLF -->|ui| GRAF
    </div>
    """,
    height=600,
)

st.divider()

st.markdown('<p class="sub-header">2. Volumes partagés</p>', unsafe_allow_html=True)
st.markdown("Les volumes permettent aux services de **partager des données sans couplage direct**.")

volumes = {
    "accidents-data": "Données préprocessées (X_train, X_test, y_train, y_test). Écrit par `preprocess`, lu par `train`, `airflow` et le service de drift.",
    "postgres-airflow-data": "État persistant d'Airflow (DAGs, runs, logs de tâches).",
    "airflow-logs": "Logs des tâches Airflow, montés dans le conteneur pour consultation.",
    "prometheus_data": "Séries temporelles Prometheus, conservées entre redémarrages.",
    "grafana_data": "Dashboards et configuration Grafana.",
}

for name, desc in volumes.items():
    st.markdown(
        f"<div class='service-card'><strong>{name}</strong> — {desc}</div>",
        unsafe_allow_html=True,
    )

st.divider()

st.markdown('<p class="sub-header">3. Images construites sur mesure</p>', unsafe_allow_html=True)
st.markdown(
    "Quatre services utilisent un **Dockerfile dédié** plutôt qu'une image publique, "
    "pour embarquer le code et les dépendances du projet :"
)

st.code(
    """
# Lancer tout le projet
docker compose up --build

# Images construites localement :
# - Dockerfile.airflow       → service airflow + airflow-init
# - src/preprocess/Dockerfile → service preprocess
# - src/train/Dockerfile      → service train
# - src/bentoml/Dockerfile    → service ml-api
# - src/streamlit/Dockerfile  → service streamlit
# - src/nginx/Dockerfile      → service nginx
    """,
    language="bash",
)

st.markdown("### Pourquoi Docker Compose ici ?")
st.info(
    "Docker Compose garantit que tous les services démarrent dans le bon ordre (grâce aux `depends_on` et `healthcheck`), "
    "que les variables d'environnement sont cohérentes, et qu'un nouveau membre de l'équipe peut lancer "
    "l'intégralité du projet en une seule commande, sans installer MLflow, Airflow ou Prometheus localement."
)

st.success(
    "Docker est le socle sur lequel repose toute la reproductibilité du projet : "
    "même environnement en dev, en CI et en production."
)

