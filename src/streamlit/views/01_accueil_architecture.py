import streamlit as st
import streamlit_mermaid as stmd

# Configuration de la page
st.set_page_config(
    page_title="MLOps Accidents",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STYLE ---
st.markdown("""
    <style>
    .main-header {font-size: 3rem; font-weight: bold; color: #1f77b4; margin-bottom: 0.5rem; text-align: left;}
    .sub-header {font-size: 1.5rem; font-weight: 600; color: #2c3e50; margin-top: 2rem;}
    .arch-box {background-color: #f8f9fa; padding: 1.5rem; border-radius: 10px; border: 1px solid #e9ecef; height: 100%;}
    .nav-button {display: block; width: 100%; padding: 1rem; margin: 0.5rem 0; background-color: #1f77b4; color: white; text-align: center; text-decoration: none; border-radius: 8px; font-weight: bold; transition: background 0.3s;}
    .nav-button:hover {background-color: #155a8a; color: white;}
    </style>
    """, unsafe_allow_html=True)

# --- EN-TÊTE : MISSION & CONTEXTE ---
st.markdown('<p class="main-header">Prédiction de gravité des accidents</p>', unsafe_allow_html=True)

st.markdown("""
**Mission :** Déployer une infrastructure MLOps capable de prédire en temps réel si un accident nécessite une intervention **prioritaire**, afin d'optimiser l'envoi des secours.  
""")

st.divider()

# --- SECTION 1 : L'ARCHITECTURE GLOBALE ---
st.info("""
**Etapes clés et architecture de projet :**
1.  **Exploration des données :** Analyse et préparation des données sources.
2.  **CI/CD (GitHub Actions) & GitHub Projects :** Gestion de la chaîne de déploiement et de la gestion des projets.
3.  **Déploiement (Docker) :** Conteneurise chaque composant.
4.  **Orchestration (Airflow) :** Planifie l'ingestion et l'entraînement.
5.  **Tracking (MLflow) :** Enregistre les modèles et les métriques de performance.
6.  **Serving (BentoML) :** Expose le modèle "Champion" via une API sécurisée.
7.  **Accès (Nginx + Streamlit) :** Fournit une interface utilisateur HTTPS protégée.
8.  **Monitoring (Prometheus + Grafana) :** Surveille la santé du service et la dérive du modèle.
9.  **Drift monitoring (Airflow):** Détecte les changements dans la distribution des données.
""")