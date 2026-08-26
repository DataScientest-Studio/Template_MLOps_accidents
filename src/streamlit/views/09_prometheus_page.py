import streamlit as st

# Configuration de la page
st.set_page_config(
    page_title="MLOps Accidents - Monitoring Prometheus",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- STYLE PERSONNALISÉ ---
st.markdown("""
    <style>
    .main-header {font-size: 2.5rem; font-weight: bold; color: #1f77b4; margin-bottom: 1rem;}
    .sub-header {font-size: 1.5rem; font-weight: 600; color: #2c3e50; margin-top: 2rem;}
    .metric-box {background-color: #f8f9fa; border-left: 4px solid #e6522c; padding: 1rem; margin: 0.5rem 0; border-radius: 4px;}
    </style>
    """, unsafe_allow_html=True)

# --- EN-TÊTE ---
st.markdown('<p class="main-header">Collecte de Métriques avec Prometheus</p>', unsafe_allow_html=True)

st.markdown("""
Prometheus est le cœur de notre système d'**observabilité**. Il agit comme une base de données de séries temporelles qui vient interroger (scrape) régulièrement nos services pour collecter les indicateurs de santé et de performance.
""")

st.markdown(
    "<div style='text-align:center; margin: 1rem 0;'>"
    "<a href='http://localhost:9090' target='_blank'>"
    "<button style='background-color:#28a745; color:white; border:none; padding:15px 30px; font-size:1.2rem; border-radius:5px; cursor:pointer;'>"
    "Ouvrir Prometheus</button></a>"
    "</div>",
    unsafe_allow_html=True,
)

st.divider()

# --- 1. CONFIGURATION DU SCRAPING ---
st.markdown('<p class="sub-header">1. Configuration de Collecte (`prometheus.yml`)</p>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("""
    **Stratégie de Collecte :**
    - **Fréquence :** Toutes les **15 secondes** (`scrape_interval`).
    - **Cibles Statiques :** Nous monitorons deux sources critiques :
      1.  **Prometheus lui-même** (Auto-surveillance).
      2.  **L'API BentoML** (`ml-api:3000`).
    
    **Pourquoi statique ?**
    Dans cette MVP, les services sont orchestrés par Docker Compose avec des noms de service fixes, permettant une configuration simple et robuste sans besoin de "Service Discovery" complexe.
    """)

with col2:
    st.markdown("**Extrait de configuration :**")
    st.code("""
global:
  scrape_interval: 15s  # Fréquence de collecte

scrape_configs:
  # 1. Auto-surveillance
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]

  # 2. Notre API de Prédiction
  - job_name: "bentoml-api"
    static_configs:
      - targets: ["ml-api:3000"]
    """, language="yaml")

st.divider()

# --- 2. MÉTRIQUES COLLECTÉES ---
st.markdown('<p class="sub-header">2. Métriques Exploitées</p>', unsafe_allow_html=True)

st.markdown("""
Prometheus récupère automatiquement toutes les métriques exposées par l'endpoint `/metrics` de BentoML. Nous nous concentrons sur 4 indicateurs clés pour le pilotage de notre MLOps :
""")

c1, c2 = st.columns(2)

with c1:
    st.markdown("### 📊 Métriques de Trafic (HTTP)")
    st.markdown("""
    - **`app_requests_total`** : Volume total de requêtes reçues.
      - *Labels :* `method`, `endpoint`, `status` (200, 429, 500).
      - *Usage :* Détecter les pics de charge ou les erreurs système.
    
    - **`app_request_latency_seconds`** : Temps de réponse global.
      - *Usage :* Identifier les ralentissements réseau ou de traitement.
    """)
    st.info("💡 Ces métriques permettent de calculer le **taux d'erreur** et le **temps de réponse moyen** (SLA).")

with c2:
    st.markdown("### 🤖 Métriques Métier (Modèle)")
    st.markdown("""
    - **`model_predictions_total`** : Nombre de prédictions effectuées.
      - *Labels :* `class` (0 ou 1), `status`.
      - *Usage :* Suivre la distribution des prédictions (Détection de **Data Drift**).
    
    - **`model_prediction_latency_seconds`** : Temps d'inférence pur.
      - *Usage :* Surveiller la performance du modèle seul, indépendamment du réseau.
    """)
    st.warning("⚠️ Une augmentation soudaine de la classe '1' (Prioritaire) peut alerter sur un changement de contexte (ex: accident majeur, conditions météo extrêmes).")

st.divider()

# --- 3. INTÉGRATION ARCHITECTURE ---
st.markdown('<p class="sub-header">3. Intégration dans le Flux MLOps</p>', unsafe_allow_html=True)

st.markdown("""
Dans notre architecture Docker :
1.  **Exposition :** BentoML expose les métriques sur le port 3000 (`/metrics`).
2.  **Collecte :** Prometheus (port 9090) vient interroger BentoML toutes les 15s.
3.  **Stockage :** Les données sont stockées localement (`prometheus_data`) pour l'historique.
4.  **Visualisation :** Ces données brutes sont ensuite envoyées à **Grafana** pour être transformées en dashboards lisibles.
""")

# Schéma de flux de données
mermaid_data = """
flowchart LR
    Bento["BentoML API<br/>(Expose /metrics)"] -->|HTTP GET| Promo["((Prometheus<br/>Scrape toutes les 15s))"]
    Promo -->|Stockage TSDB| Disk[(Volume Docker<br/>prometheus_data)]
    Promo -->|Requêtes PromQL| Graf["Grafana<br/>Dashboarding"]
    
    style Promo fill:#e6522c,stroke:#c43a1c,color:white
    style Bento fill:#f8f9fa,stroke:#6c757d
    style Graf fill:#f8f9fa,stroke:#6c757d
"""
st.mermaid_chart(mermaid_data)

st.success("""
✅ **Prometheus est opérationnel.** 
Il collecte activement les métriques de notre API. La prochaine étape (page suivante) est la visualisation de ces données dans Grafana et la configuration des alertes.
""")