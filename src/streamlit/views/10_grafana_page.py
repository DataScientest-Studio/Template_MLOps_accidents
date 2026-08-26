import streamlit as st

# Configuration de la page
st.set_page_config(
    page_title="MLOps Accidents - Grafana",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- STYLE PERSONNALISÉ ---
st.markdown("""
    <style>
    .main-header {font-size: 2.5rem; font-weight: bold; color: #1f77b4; margin-bottom: 1rem;}
    .sub-header {font-size: 1.5rem; font-weight: 600; color: #2c3e50; margin-top: 2rem;}
    .query-box {background-color: #2b2b2b; color: #f8f8f2; padding: 10px; border-radius: 5px; font-family: monospace; font-size: 0.9em; border-left: 4px solid #e6522c;}
    .alert-badge {display: inline-block; background-color: #f8d7da; color: #721c24; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.85em; margin-right: 5px;}
    </style>
    """, unsafe_allow_html=True)

# --- EN-TÊTE ---
st.markdown('<p class="main-header">Visualisation & Alerting avec Grafana</p>', unsafe_allow_html=True)

st.markdown("""
Grafana transforme les métriques brutes de Prometheus en indicateurs visuels et déclenche des alertes automatiques. 
Toute l'instance est déployée **"As Code"** : aucun clic manuel, tout est versionné et automatisé au démarrage.
""")

# Bouton d'accès rapide
st.markdown(
    "<div style='text-align:center; margin: 1.5rem 0;'>"
    "<a href='http://localhost:3000' target='_blank'>"
    "<button style='background-color:#F46800; color:white; border:none; padding:12px 24px; font-size:1.1rem; border-radius:6px; cursor:pointer; font-weight:bold; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>"
    "📊 Ouvrir le Dashboard Grafana</button></a>"
    "</div>",
    unsafe_allow_html=True,
)

st.divider()

# --- 1. SOURCE DE DONNEES PROMETHEUS ---
st.markdown('<p class="sub-header">1. Source de données : Prometheus</p>', unsafe_allow_html=True)

st.markdown("""
    Nous utilisons **Prometheus** comme source principale, pour sa compatibilité native avec les métriques exposées par BentoML et Nginx.
    Grafana interroge cette base de séries temporelles pour générer les visualisations en temps réel.
    """)

st.caption("""💡**Déploiement :** La connexion est configurée automatiquement via **`datasources.yml`** au lancement du container. Aucune saisie manuelle d'URL n'est nécessaire.
    """)
st.code("""
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    url: http://prometheus:9090
    isDefault: true
    """, language="yaml")

st.divider()

# --- 2. DASHBOARD "MLOPS" ---
st.markdown('<p class="sub-header">2. Dashboard</p>', unsafe_allow_html=True)

st.markdown("Notre dashboard centralisé (`mlops-dashboard.json`) répond à 4 questions pour l'opération du modèle :")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**📊 Indicateurs de Santé**")
    st.info("""
    1.  **Taux d'Erreur** (`/predict`) : Cible < 1% (Warning), > 5% (Critique). Un pic signale un bug ou des données malformées.
    2.  **Latence p95** : Temps de réponse pour 95% des requêtes. Une hausse indique une saturation ou un modèle trop lourd.
    """)

with col2:
    st.markdown("**🤖 Indicateurs Métier**")
    st.success("""
    3.  **Distribution des Prédictions** : Ratio Classe 0 vs 1. Une dérive soudaine peut indiquer un **Data Drift**.
    4.  **Trafic Global (Requêtes par seconde)** : Permet de dimensionner l'infrastructure et de corréler les erreurs avec les pics de charge.
    """)

st.caption("💡 **Déploiement :** Le dashboard est importé automatiquement via `dashboards.yml` qui scanne le dossier de provisioning au démarrage.")

st.divider()

# --- 3. ALERTES AUTOMATISÉES ---
st.markdown('<p class="sub-header">3. Alertes & Notifications</p>', unsafe_allow_html=True)

st.markdown("""
Pour réagir proactivement, deux règles d'alerte critiques sont déployées via notre script d'initialisation (`init_grafana_alerts.py`).
""")

c_alert1, c_alert2 = st.columns(2)

with c_alert1:
    st.markdown("**🚨 Alerte 1 : Taux d'Erreur Élevé**")
    st.markdown("""
    - **Seuil :** > 5% sur 5 min.
    - **Signification :** Le service est instable ou les données sont invalides.
    """)
    # AJOUT : La requête technique réelle
    st.code("""
sum(rate(app_requests_total{status="error"}[5m])) 
/ 
sum(rate(app_requests_total[5m])) > 0.05
    """, language="text")

with c_alert2:
    st.markdown("**🐢 Alerte 2 : Latence Excessive**")
    st.markdown("""
    - **Seuil :** p95 > 2 secondes.
    - **Signification :** Le modèle est trop lent, risque de timeout.
    """)
    # AJOUT : La requête technique réelle
    st.code("""
histogram_quantile(0.95, rate(
  model_prediction_latency_seconds_bucket[5m]
)) > 2.0
    """, language="text")

# REMPLACEMENT : Schéma technique plus pertinent
st.markdown("**🔄 Flux d'Alerting Automatisé**")
mermaid_code = """
graph LR
    Script[Script init_grafana_alerts.py] -->|1. API Call| Grafana[(Grafana)]
    Grafana -->|2. Détection| Rule[Règle PromQL]
    Rule -->|3. Trigger| Webhook[Webhook Discord]
    Webhook -->|4. Notification| Team[Équipe Ops]
    
    style Script fill:#e3f2fd,stroke:#1f77b4
    style Grafana fill:#f46800,stroke:#333,color:white
    style Team fill:#d4edda,stroke:#28a745
"""
st.mermaid_chart(mermaid_code)

# FUSION : Notifications + Déploiement
st.info("""
💡 **Déploiement & Notifications :**
Au lancement, le service `grafana-init` exécute un script Python qui :
1.  Crée le dossier "MLOps_Alerts".
2.  Configure le point de contact **Discord** (via API). L'URL du webhook est injectée dynamiquement via `DISCORD_WEBHOOK_URL` pour sécuriser le secret.
3.  Pousse les règles d'alertes JSON via l'API de provisioning.

*Résultat : Une chaîne d'alerting opérationnelle dès la première seconde, sans configuration manuelle.*
""")

st.divider()

# --- SYNTHÈSE ---
st.success("""
✅ **Grafana est opérationnel.** 
Il fournit une visibilité temps réel sur la santé du modèle et garantit qu'aucune anomalie critique (erreur, latence) ne passe inaperçue grâce à une chaîne d'alerting entièrement automatisée de bout en bout.
""")