import streamlit as st

st.set_page_config(
    page_title="Data Drift - Monitoring",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .main-header {font-size: 2.8rem; font-weight: bold; color: #6f42c1; margin-bottom: 0.75rem;}
    .sub-header {font-size: 1.5rem; font-weight: 600; color: #333; margin-top: 1.75rem;}
    .info-box {background-color: #f3f0ff; border-left: 5px solid #6f42c1; padding: 1rem; border-radius: 8px; margin: 1rem 0;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<p class="main-header">Data Drift : surveillance des données</p>', unsafe_allow_html=True)
st.markdown(
    "Un modèle peut se dégrader sans jamais planter — simplement parce que les **données en production "
    "s'éloignent des données d'entraînement**. Le DAG `drift_monitoring` surveille ce phénomène automatiquement, "
    "chaque semaine, directement dans Airflow."
)

st.markdown(
    "<div style='text-align:center; margin: 1rem 0;'>"
    "<a href='http://localhost:8080' target='_blank'>"
    "<button style='background-color:#6f42c1; color:white; border:none; padding:15px 30px; font-size:1.2rem; border-radius:5px; cursor:pointer;'>"
    "Voir le DAG dans Airflow</button></a>"
    "</div>",
    unsafe_allow_html=True,
)

st.divider()

st.markdown('<p class="sub-header">1. Qu\'est-ce que le data drift ?</p>', unsafe_allow_html=True)
st.markdown(
    """
    Le **data drift** désigne le changement statistique de la distribution des données d'entrée au fil du temps.
    Par exemple, si la répartition des vitesses de véhicules impliqués dans des accidents change d'une saison à l'autre,
    le modèle entraîné sur d'anciennes données peut devenir moins fiable — sans qu'aucune erreur technique ne se déclenche.

    Détecter le drift tôt permet de **décider si un réentraînement est nécessaire** avant que les prédictions ne se dégradent.
    """
)

st.divider()

st.markdown('<p class="sub-header">2. DAG : <code>drift_monitoring</code></p>', unsafe_allow_html=True)
st.markdown(
    "Le DAG s'exécute **chaque semaine** (`@weekly`) et se déclenche aussi **automatiquement** "
    "à la fin du pipeline principal `mlops_accident_gravity_pipeline` (via `TriggerDagRunOperator`). "
    "Il contient deux tâches :"
)

col1, col2 = st.columns(2)
with col1:
    st.markdown("**1. `compute_drift`**")
    st.write(
        "Compare la distribution de chaque feature numérique entre "
        "`X_train.csv` (référence) et `X_test.csv` (données courantes). "
        "Deux métriques sont calculées par feature : le test KS et le PSI."
    )
with col2:
    st.markdown("**2. `alert_on_drift`**")
    st.write(
        "Analyse le rapport produit par `compute_drift`. "
        "Si plus de **30 % des features** sont en drift, la tâche échoue "
        "et une alerte remonte dans l'UI Airflow pour signaler qu'un réentraînement est recommandé."
    )

st.divider()

st.markdown('<p class="sub-header">3. Les métriques utilisées</p>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.markdown("#### Test de Kolmogorov-Smirnov (KS)")
    st.markdown(
        """
        Compare deux distributions en mesurant l'écart maximal entre leurs fonctions de répartition.
        - **p-value < 0.05** → drift détecté sur cette feature
        - Non-paramétrique : fonctionne sans hypothèse sur la forme de la distribution
        """
    )
with col2:
    st.markdown("#### Population Stability Index (PSI)")
    st.markdown(
        """
        Mesure le déplacement global d'une distribution via des histogrammes.
        - **PSI < 0.1** → pas de drift significatif
        - **0.1 ≤ PSI < 0.2** → drift modéré, à surveiller
        - **PSI ≥ 0.2** → drift significatif détecté
        """
    )

st.markdown(
    "<div class='info-box'>Une feature est marquée <strong>en drift</strong> si <em>au moins un</em> des deux tests le détecte "
    "(p-value KS &lt; 0.05 <strong>OU</strong> PSI &gt; 0.2). Cette double vérification réduit les faux négatifs.</div>",
    unsafe_allow_html=True,
)

st.divider()

st.markdown('<p class="sub-header">4. Code clé</p>', unsafe_allow_html=True)
st.code(
    """
# Pour chaque feature numérique :
ks_stat, p_value = stats.ks_2samp(ref_vals, cur_vals)
psi = _psi(ref_vals, cur_vals)

has_drift = (p_value < 0.05) or (psi > 0.2)

# Alerte si ≥ 30% des features sont en drift
drift_ratio = len(drifted) / total
if drift_ratio >= 0.3:
    raise RuntimeError("ALERTE DRIFT : réentraînement recommandé.")
    """,
    language="python",
)

st.divider()

st.markdown('<p class="sub-header">5. Intégration dans le pipeline</p>', unsafe_allow_html=True)
st.markdown(
    """
    Le drift monitoring n'est pas isolé : il est **branché en fin du pipeline principal**.
    Après chaque cycle mensuel (prétraitement → entraînement → évaluation → promotion),
    Airflow déclenche automatiquement `drift_monitoring` pour vérifier que les nouvelles données
    restent cohérentes avec la référence.

    ```
    preprocess → train → evaluate_metrics → promote_model
                                          ↘ reload_predict_service
                                                     ↘ trigger_drift_monitoring
    ```
    """
)

st.success(
    "Le data drift est la première ligne de défense contre la dégradation silencieuse du modèle en production. "
    "En l'automatisant dans Airflow, l'équipe est alertée sans intervention manuelle."
)
