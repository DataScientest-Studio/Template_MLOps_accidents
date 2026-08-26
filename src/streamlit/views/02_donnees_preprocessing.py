import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

# Configuration de la page
st.set_page_config(
    page_title="MLOps Accidents - Données & Préprocessing",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- STYLE PERSONNALISÉ ---
st.markdown("""
    <style>
    .main-header {font-size: 2.5rem; font-weight: bold; color: #1f77b4; margin-bottom: 1rem;}
    .sub-header {font-size: 1.5rem; font-weight: 600; color: #2c3e50; margin-top: 2rem;}
    .highlight-box {background-color: #e8f4fd; border-left: 5px solid #1f77b4; padding: 1rem; border-radius: 4px; margin: 1rem 0;}
    </style>
    """, unsafe_allow_html=True)

# --- EN-TÊTE : VISION GLOBALE (Fusion Objectif + Défi) ---
st.markdown('<p class="main-header">Données & Préprocessing</p>', unsafe_allow_html=True)

# --- CONTEXTE & SOURCES ---

st.markdown('<p class="sub-header">1. Contexte Data & Stratégie de Cible</p>', unsafe_allow_html=True)

# Métriques
col_stat1, col_stat2, col_stat3, col_stat4, col_stat5 = st.columns(5)
with col_stat1:
    st.metric(label="Usagers", value="~506k")
with col_stat2:
    st.metric(label="Véhicules", value="~378k")
with col_stat3:
    st.metric(label="Accidents", value="~221k")
with col_stat4:
    st.metric(label="Lieux", value="~253k")
with col_stat5:
    st.metric(label="Période (Uniformité des formats)", value="2021-2024")

st.markdown("""
- **Source :** Bases de Données Annuelles des Accidents Corporels de la Circulation Routière ([Fichier BAAC - data.gouv.fr - ONISR](https://www.data.gouv.fr/datasets/bases-de-donnees-annuelles-des-accidents-corporels-de-la-circulation-routiere-annees-de-2005-a-2024)).
- **Fréquence :** Mise à jour annuelle
- **Structure :** 4 fichiers CSV interconnectés par `Num_Acc` (ID Accident) et `id_vehicule` :""")

with st.expander("🔍 Détails des informations disponibles", expanded=True):

    tab1, tab2, tab3, tab4 = st.tabs(["Usagers", "Véhicules", "Caract.", "Lieux"])

    with tab1:
        st.markdown("""
        - Données personnelles des victimes : Année de naissance, Sexe
        - Contexte : Motif du déplacement (ex : Domicile-Travail)
        - Implication : Piéton/Conducteur/Passager, place dans le véhicule ou localisation si piéton, port d'équipements de sécurité (ceinture, casque)
        - Gravité de blessure : Indemne, Blessé léger, Blessé hospitalisé, Tué
        - Clés : `Num_Acc`, `id_vehicule`, `id_usager`
        """)
    with tab2:
        st.markdown("""
            - Caractéristiques  (mécaniques) : Catégorie, Carburant, Motorisation
            - Contexte de l'accident : Manœuvre, Type de collision, Position du véhicule
            - Clés : `Num_Acc`, `id_vehicule`
            """)
    with tab3:
        st.markdown("""
        - Sens de circulation, Catégorie de route, Nombre de voies, Voies réservées, Pente, Tracé, Terre-plein, Surface (mouillée, verglas, etc.), Infrastructure (Pont, Tunnel), Situation (chaussé, piste cyclable...)
        - Clés : `Num_Acc`
        """)
    with tab4:
        st.markdown("""
        - Date, Heure, Eclairage et Météo
        - Département, Commune, (Latitude / Longitude, Adresse)
        - Agglomération / hors, Type d'intersection
        - Type de collision
        - Clés : `Num_Acc`
        """)

st.info("""
La prédiction doit déterminer la priorité selon le cas le plus grave des usagers impliquées dans l'accident :
- 🔴 **Classe 1 (Prioritaire)** : **Au moins un** Tué **ou** Hospitalisé.
- 🟢 **Classe 0 (Non-Prioritaire)** : **Uniquement** Indemnes **et / ou** Blessés légers.
""")

st.divider()

# --- 2. PIPELINE DATA ENGINEERING ---

st.markdown('<p class="sub-header">2. Pipeline de preprocessing (`preprocess.py`)</p>', unsafe_allow_html=True)

st.markdown("Le défi technique majeur est la **granularité multiple** (1 Accident = N Véhicules = M Usagers).")

# Schéma Mermaid
mermaid_code = """
flowchart LR
    A[Sources Brutes] -->|Fusion Usagers+Véhicules| B(1. RÉDUCTION\nTri Gravité + DropDuplicates)
    B -->|1 ligne / accident| C{2. FUSION FINALE\n+ Lieux + Caract.}
    C -->|Recodage Cible| D[Dataset ML\n184k lignes]
    
    style A fill:#e3f2fd,stroke:#1f77b4,stroke-width:2px
    style B fill:#fff3cd,stroke:#ffc107,stroke-width:4px
    style C fill:#d4edda,stroke:#28a745,stroke-width:2px
    style D fill:#c3e6cb,stroke:#0c5460,stroke-width:2px
"""
st.mermaid_chart(mermaid_code)

# Détails techniques (Expander allégé)
with st.expander("🔍 Détails techniques des transformations", expanded=False):
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("**A. Fusion & Réduction (Le cœur du pipeline)**")
        st.code("""
# 1. Fusion Usagers + Véhicules (N lignes)
fusion1 = df_users.merge(df_veh, on=['Num_Acc', 'id_vehicule'])

# 2. Correction codes gravité (Spécificité BAAC)
fusion1['grav'] = fusion1['grav'].replace([2, 4], [4, 2])

# 3. Réduction : On garde la ligne la plus grave par accident
fusion1 = fusion1.sort_values(by='grav', ascending=False)
df_unique = fusion1.drop_duplicates(subset=['Num_Acc'], keep='first')

# 4. Fusion finale avec Lieux et Caractéristiques (1:1)
df_final = df_unique.merge(df_lieux, on='Num_Acc').merge(df_caract, on='Num_Acc')
        """, language="python")
        
    with c2:
        st.markdown("**B. Nettoyage & Cible Binaire**")
        st.code("""
# Recodage final de la cible (Ligne 214)
# 1 (Indemne) -> 0
# 2 (Blessé léger) -> 0  <-- Après inversion précédente
# 3 (Hospitalisé) -> 1
# 4 (Tué) -> 1          <-- Après inversion précédente
df_final['grav'] = df_final['grav'].replace([1, 2, 3, 4], [0, 0, 1, 1])

# Nettoyage : Drop IDs, Adresses, et lignes NaN critiques
        """, language="python")

st.info("⚠️ **Point Critique MLOps :** La réduction à 1 ligne/accident se fait par **tri décroissant de gravité** suivi d'un `drop_duplicates`. Cela garantit de conserver le cas le plus grave (ex: 1 Tué + 3 Indemnes = Accident Prioritaire).")

col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    st.metric("Accidents Uniques", "~184k")
with col_f2:
    st.metric("Features Sélectionnées", "28")
with col_f3:
    st.metric("Distribution : Classes 0 / 1", "66% / 34%")

# --- TRANSPARENCE MÉTHODOLOGIQUE ---
st.warning("""
⚠️ **Choix Méthodologique (Périmètre MLOps) :**
L'objectif principal de ce projet étant la validation d'une **architecture MLOps microservices** (Docker, Orchestration, Monitoring), nous avons volontairement limité le *Feature Engineering* avancé.
- **Split Train/Test :** Un split aléatoire (`train_test_split`) a été privilégié pour cette MVP.
- **Évolutivité :** Split temporel nécessaire pour une mise en production réelle et éviter les fuites de données sur des séries temporelles.
""")

st.divider()

# --- 3. BLOC INDUSTRIALISATION ---
st.markdown('<p class="sub-header">3. Industrialisation & Orchestration Docker</p>', unsafe_allow_html=True)

col_dock1, col_dock2 = st.columns([1, 2])

with col_dock1:
    st.markdown("""
    **Architecture Microservices :**
    - 📦 **Container Dédié :** Le preprocessing s'exécute dans un container isolé (`src/preprocess/Dockerfile`).
    - 🔗 **Orchestration :** Lancé par `docker-compose` avant l'entraînement.
    - 💾 **Persistance :** Les données nettoyées sont écrites sur un volume partagé (`accidents-data`) consommé par l'étape suivante.
    """)
    st.code("""
services:
  preprocess:
    build: ./src/preprocess
    volumes:
      - accidents-data:/app/data
    restart: "no" # Run once

  train:
    depends_on:
      preprocess:
        condition: service_completed_successfully
    """, language="yaml")

with col_dock2:
    # Petit schéma Mermaid pour l'orchestration
    mermaid_orch = """
    flowchart TD
        P[Container Preprocess<br/>🐍 Python Script] -->|Écrit données| V[(Volume Docker<br/>accidents-data)]
        V -->|Lit données| T[Container Train<br/>🤖 ML Model]
        
        style P fill:#e3f2fd,stroke:#1f77b4
        style V fill:#fff3cd,stroke:#ffc107,stroke-dasharray: 5 5
        style T fill:#d4edda,stroke:#28a745
        
        subgraph Orchestration
        direction TB
        P -.->|condition: completed_successfully| T
        end
    """
    st.mermaid_chart(mermaid_orch)
    st.caption("Le container 'Train' ne démarre que si 'Preprocess' termine avec succès (Exit Code 0).")