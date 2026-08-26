import streamlit as st

# Configuration de la page
st.set_page_config(
    page_title="MLOps Accidents - Serving BentoML",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- STYLE PERSONNALISÉ ---
st.markdown("""
    <style>
    .main-header {font-size: 2.5rem; font-weight: bold; color: #1f77b4; margin-bottom: 1rem;}
    .sub-header {font-size: 1.5rem; font-weight: 600; color: #2c3e50; margin-top: 2rem;}
    .metric-card {background-color: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #e9ecef;}
    </style>
    """, unsafe_allow_html=True)

# --- EN-TÊTE ---
st.markdown('<p class="main-header">Serving de Modèle avec BentoML</p>', unsafe_allow_html=True)

st.markdown("""
BentoML est le cœur de notre architecture de **Serving**. Il transforme le modèle entraîné (MLflow) en une API microservice robuste, conteneurisée et instrumentée pour le monitoring.
""")

st.divider()

# --- 1. RÔLE DANS L'ARCHITECTURE ---
st.markdown('<p class="sub-header">1. Positionnement & Flux de Données</p>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("""
    **Fonctions Clés :**
    - 📦 **Conteneurisation :** Image Docker dédiée (`src/bentoml/Dockerfile`).
    - 🔄 **Chargement Dynamique :** Récupère le modèle "Champion" depuis MLflow au démarrage.
    - 🚀 **API Haute Performance :** Exposition native d'endpoints (`/predict`, `/reload_model`).
    - 📊 **Instrumentation :** Exposition native des métriques Prometheus (`/metrics`).
    """)

with col2:
    # Schéma du flux BentoML
    mermaid_flow = """
    flowchart LR
        Airflow["Airflow<br/>Orchestrateur"] -->|Trigger & Reload| Bento
        MLflow["MLflow<br/>Registry"] -->|Load Model| Bento
        Bento["((BentoML Service<br/>Port 3000))"] -->|Expose /metrics| Promo["Prometheus"]
        Bento -->|Serve Predictions| Nginx["Nginx / Frontend"]
        
        style Bento fill:#e3f2fd,stroke:#1f77b4,stroke-width:3px
        style MLflow fill:#f8f9fa,stroke:#6c757d
        style Airflow fill:#f8f9fa,stroke:#6c757d
        style Promo fill:#f8f9fa,stroke:#6c757d
        style Nginx fill:#f8f9fa,stroke:#6c757d
    """
    st.mermaid_chart(mermaid_flow)
    st.caption("BentoML agit comme le pont entre le Registry (MLflow), l'Orchestrateur (Airflow) et le Monitoring.")

st.divider()

# --- 2. ENDPOINTS & LOGIQUE MÉTIER ---
st.markdown('<p class="sub-header">2. Endpoints Exposés (`service.py`)</p>', unsafe_allow_html=True)

tab_pred, tab_reload = st.tabs(["🔮 /predict (Inférence)", "🔄 /reload_model (Mise à jour)"])

with tab_pred:
    st.markdown("""
    **Endpoint :** `POST /predict`
    
    **Logique :**
    1.  **Validation :** Vérification stricte du schema d'entrée via **Pydantic** (28 features attendues).
    2.  **Inférence :** Prédiction temps réel avec le modèle Scikit-Learn chargé en mémoire.
    3.  **Observabilité :** 
        - Incrémentation du compteur `model_predictions_total` (succès/erreur/classe).
        - Mesure de la latence d'inférence (`model_prediction_latency_seconds`).
    
    **Exemple de Payload :**
    """)
    st.code("""
{
  "place": 1, "catu": 2, "sexe": 1, "secu1": 2, 
  "year_acc": 2023, "victim_age": 35, "catv": 1, 
  ... (21 autres features) ...
  "nb_victim": 1, "nb_vehicules": 1
}
    """, language="json")

with tab_reload:
    st.markdown("""
    **Endpoint :** `GET /reload_model`
    
    **Cas d'usage :** Appelé automatiquement par **Airflow** après un ré-entraînement réussi.
    
    **Logique :**
    1.  Connexion à MLflow (`models:/Modèle_Gravité_Accidents@champion`).
    2.  Chargement du nouveau modèle en mémoire **sans redémarrer le container**.
    3.  Bascule immédiate vers la nouvelle version pour les requêtes suivantes.
    
    **Avantage MLOps :** Zéro downtime lors des mises en production de modèles.
    """)
    st.code("""
# Extrait service.py
@bentoml.api(route="/reload_model")
def reload_model(self) -> dict:
    self._load_model() # Charge depuis MLflow
    return {"status": "success"}
    """, language="python")

st.divider()

# --- 3. OBSERVABILITÉ & MÉTRIQUES CUSTOM ---
st.markdown('<p class="sub-header">3. Instrumentation Native pour Prometheus</p>', unsafe_allow_html=True)

st.markdown("""
Contrairement à un serveur Flask classique, BentoML permet d'exposer nativement un endpoint `/metrics` scrapé par Prometheus. Nous avons défini 4 métriques critiques :
""")

col_m1, col_m2, col_m3, col_m4 = st.columns(4)

with col_m1:
    st.markdown("**📈 Trafic API**")
    st.code("app_requests_total\n[method, endpoint, status]", language="text")
    st.caption("Surveille le volume et les erreurs HTTP globales.")

with col_m2:
    st.markdown("**⏱️ Latence API**")
    st.code("app_request_latency_seconds\n[buckets]", language="text")
    st.caption("Performance globale du service (network + processing).")

with col_m3:
    st.markdown("**🎯 Prédictions**")
    st.code("model_predictions_total\n[model, status, class]", language="text")
    st.caption("Business Metric : Volume de prédictions par classe (0 ou 1).")

with col_m4:
    st.markdown("**⚡ Latence Modèle**")
    st.code("model_prediction_latency_seconds\n[buckets]", language="text")
    st.caption("Performance pure de l'inférence (hors réseau).")