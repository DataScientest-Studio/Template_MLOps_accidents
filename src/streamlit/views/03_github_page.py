import streamlit as st

# Configuration de la page
st.set_page_config(
    page_title="MLOps Accidents - GitHub - CI/CD & Gestion de projet",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- STYLE ---
st.markdown(
    """
    <style>
    .main-header {font-size: 2.5rem; font-weight: bold; color: #1f77b4; margin-bottom: 1rem;}
    .sub-header {font-size: 1.5rem; font-weight: 600; color: #2c3e50; margin-top: 2rem;}
    .value-card {background-color: #f8f9fa; padding: 1.5rem; border-radius: 8px; border-left: 5px solid #8250df; height: 100%;}
    </style>
    """,
    unsafe_allow_html=True,
)

# --- EN-TÊTE ---
st.markdown(
    '<p class="main-header">GitHub : Qualité du code & Organisation d\'équipe</p>',
    unsafe_allow_html=True,
)

st.markdown("""
Le développement du projet s'appuie sur deux fonctionnalités de **GitHub** : l'**intégration continue**
(GitHub Actions), qui vérifie automatiquement chaque changement de code avant qu'il n'atteigne `main`,
et **GitHub Projects**, qui organise le travail de l'équipe sous forme de tableau **Kanban**.
""")

st.divider()

# --- SECTION 1 : INTÉGRATION CONTINUE ---
st.markdown(
    '<p class="sub-header">1. Intégration continue (GitHub Actions)</p>',
    unsafe_allow_html=True,
)
st.markdown("""
Le workflow `.github/workflows/ci.yml` se déclenche sur chaque `push` (toutes branches) et sur chaque
*pull request* vers `main`. Il enchaîne deux jobs, le second dépendant du succès du premier :
""")

ci_jobs = [
    {
        "Job": "compile-check",
        "Déclencheur": "push sur une branche ≠ main",
        "Rôle": "Vérifie que tous les fichiers .py du dossier src compilent (python -m py_compile)",
    },
    {
        "Job": "docker-build",
        "Déclencheur": "pull request vers main (après compile-check)",
        "Rôle": "Build de toutes les images du projet via docker compose build",
    },
]

st.dataframe(ci_jobs, use_container_width=True, hide_index=True)

col_code, col_diag = st.columns([1, 1])

with col_code:
    st.markdown("**Extrait de configuration (`ci.yml`)**")
    st.code(
        """name: CI

on:
  push:
    branches: ["**"]
  pull_request:
    branches: [main]

jobs:
  compile-check:
    if: github.ref != 'refs/heads/main'
    steps:
      - run: python -m py_compile $(find src -name "*.py")

  docker-build:
    if: github.event_name == 'pull_request'
    needs: compile-check
    steps:
      - run: docker compose build
""",
        language="yaml",
    )

with col_diag:
    st.markdown("**Logique de déclenchement**")
    st.graphviz_chart("""
    digraph CI {
        rankdir=LR;
        node [shape=box, style=filled, fontname="Arial", penwidth=2];
        edge [fontsize=10, color="#555"];

        Push [label=" git push\\n(branche de travail)", fillcolor="#24292e", fontcolor="white"];
        Compile [label=" compile-check\\npy_compile", fillcolor="#8250df", fontcolor="white"];
        PR [label=" Pull Request\\nvers main", fillcolor="#24292e", fontcolor="white"];
        Build [label=" docker-build\\ndocker compose build", fillcolor="#2da44e", fontcolor="white"];
        Merge [label=" Merge dans main", fillcolor="#0969da", fontcolor="white"];

        Push -> Compile;
        PR -> Compile;
        Compile -> Build [label="needs"];
        Build -> Merge [label="si succès"];
    }
    """)

st.info("""
**Pourquoi deux jobs séparés ?** Le `compile-check` donne un retour très rapide (quelques secondes) à chaque
push sur une branche de travail, pendant que le `docker-build`, plus coûteux, ne s'exécute qu'au moment de la
*pull request* vers `main` — là où la fiabilité de la stack Docker complète compte réellement.
""")

st.link_button(
    "Voir les exécutions CI (GitHub Actions)",
    "https://github.com/aupaysdesdata/MLOps_accidents/actions",
    use_container_width=True,
)

st.divider()

# --- SECTION 2 : GESTION DE PROJET (KANBAN) ---
st.markdown(
    '<p class="sub-header">2. Gestion de projet (GitHub Projects / Kanban)</p>',
    unsafe_allow_html=True,
)
st.markdown("""
Le travail d'équipe est réparti et suivi via un tableau **Kanban GitHub Projects**, directement lié aux
*issues* et *pull requests* du dépôt. Chaque membre de l'équipe développe sur sa propre branche
 avant de proposer une *pull request* vers `main`.
""")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### Colonnes du board")
    st.markdown("""
    - **To do** : tâches identifiées, pas encore prises en charge.
    - **In progress** : tâche en cours de développement sur une branche personnelle.
    - **In review** : *pull request* ouverte, en attente de relecture.
    - **Done** : *pull request* mergée dans `main`, CI passée.
    """)
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("### Suivi du board")
    st.markdown("""
    Chaque carte du board est liée à une *issue* ou une *pull request* GitHub.
    - Le déplacement des cartes n'est pas automatisé.
    - Les colonnes sont mises à jour **manuellement**, à chaque réunion d'équipe.
    - Le statut CI (✅/❌) de la PR associée reste consultable directement sur GitHub.
    """)
    st.markdown("</div>", unsafe_allow_html=True)

with col3:
    st.markdown("### Travail d'équipe")
    st.markdown("""
    - Une branche par contributeur → développement en parallèle sans blocage.
    - Les tâches du board sont réparties par brique du projet
      (Airflow, MLflow, BentoML, Nginx, Monitoring, Streamlit...).
    - La CI agit comme un filet de sécurité commun avant tout merge.
    """)
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()

st.success("""
**Synthèse :**
GitHub structure à la fois la **qualité du code** (CI/CD via Actions, aucun merge sans build réussi,
versioning de tout le code du projet) et l'**organisation humaine** du projet (Kanban Projects suivi
manuellement en réunion, une branche par personne, revue par *pull request*).
Ces deux automatisations permettent à une équipe de plusieurs contributeurs d'avancer en parallèle sur des
briques différentes tout en gardant `main` toujours fonctionnel.
""")

st.link_button(
    "Ouvrir le board GitHub Projects",
    "https://github.com/aupaysdesdata/MLOps_accidents/projects",
    use_container_width=True,
)
