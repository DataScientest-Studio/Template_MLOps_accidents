import streamlit as st

st.set_page_config(
    page_title="MLOps Accidents - MLflow / Entraînement",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .main-header {font-size: 2.8rem; font-weight: bold; color: #1f77b4; margin-bottom: 0.75rem;}
    .sub-header {font-size: 1.5rem; font-weight: 600; color: #333; margin-top: 1.75rem;}
    .info-box {background-color: #fff9db; border-left: 5px solid #d6a700; padding: 1rem; border-radius: 8px; margin: 1rem 0;}
    .code-box {background-color: #f7f7f7; padding: 1rem; border-radius: 8px; border: 1px solid #e0e0e0;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<p class="main-header">MLflow : suivi des expériences et modèle champion</p>', unsafe_allow_html=True)
st.markdown(
    "MLflow trace les métriques, enregistre le modèle, puis le promeut dans le registry si la qualité est suffisante."
)

st.markdown(
    "<div style='text-align:center; margin: 1rem 0;'>"
    "<a href='http://localhost:5000' target='_blank'>"
    "<button style='background-color:#28a745; color:white; border:none; padding:15px 30px; font-size:1.2rem; border-radius:5px; cursor:pointer;'>"
    "Ouvrir MLflow UI</button></a>"
    "</div>",
    unsafe_allow_html=True,
)

st.divider()

st.markdown('<p class="sub-header">1. Expérience et métriques</p>', unsafe_allow_html=True)
st.markdown(
    """
    Le script `src/train/train_model.py` démarre un run MLflow nommé `Random Forest` dans l'expérience `Gravité_Accidents`.
    Il enregistre les métriques suivantes : `accuracy`, `precision`, `recall`, `f1_score`.
    """
)

m_col1, m_col2, m_col3, m_col4 = st.columns(4)
m_col1.metric("Accuracy", "81.19 %")
m_col2.metric("Precision", "80.85 %")
m_col3.metric("Recall", "81.19 %")
m_col4.metric("F1-Score", "80.88 %")

st.code(
    """
with mlflow.start_run(run_name='Random Forest') as run:
    rf_classifier.fit(X_train, y_train)
    mlflow.log_metric('accuracy', accuracy)
    mlflow.log_metric('precision', precision_score)
    mlflow.log_metric('recall', recall_score)
    mlflow.log_metric('f1_score', f1_score)
    mlflow.sklearn.log_model(
        rf_classifier,
        artifact_path='random_forest_model',
        registered_model_name='Modèle_Gravité_Accidents',
    )
""",
    language="python",
)

st.markdown('<p class="sub-header">2. Modèle enregistré et versionné</p>', unsafe_allow_html=True)
st.markdown(
    """
    À chaque exécution, MLflow crée un nouveau run et enregistre un artefact `random_forest_model`.
    Le modèle est également enregistré dans le Registry sous le nom `Modèle_Gravité_Accidents`.
    """
)

st.markdown("### Cycle de vie du modèle")
cols = st.columns(4)
cols[0].metric("Expérience", "Gravité_Accidents")
cols[1].metric("Modèle Registry", "Modèle_Gravité_Accidents")
cols[2].metric("Dernier run", "dernier ID enregistré")
cols[3].metric("Alias champion", "@champion")

st.markdown('<p class="sub-header">3. Validation et promotion</p>', unsafe_allow_html=True)
st.markdown(
    """
    Le DAG `evaluate_metrics` compare le modèle fraîchement entraîné avec le champion actuel sur le même jeu de validation.
    Si le nouveau modèle est au moins aussi performant, Airflow promeut la version comme `@champion` dans le Registry.
    """
)

st.info(
    "Le mécanisme de promotion garantit que la production ne reçoit que des modèles validés, et non simplement le dernier modèle entraîné."
)

st.markdown('<p class="sub-header">4. Interface MLflow</p>', unsafe_allow_html=True)
st.markdown(
    """
    - UI Tracking : http://localhost:5000
    - Visualisation des runs, des métriques et des artefacts
    - Exploration du modèle enregistré et de ses versions
    """
)

st.markdown('<p class="sub-header">5. Bonnes pratiques</p>', unsafe_allow_html=True)
st.write(
    """
    - Toujours vérifier que le `DATA_DIR` utilisé par le training correspond au volume Airflow.
    - Surveiller les metrics `f1_score` et `recall` pour éviter des modèles sur-optimistes.
    - Utiliser l’alias `@champion` pour déployer uniquement des versions validées.
    """
)

st.success(
    "MLflow ne se contente pas de stocker : il apporte de la transparence, du versioning et une gouvernance claire du modèle."
)
