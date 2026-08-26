import streamlit as st

# Configuration de la page
st.set_page_config(
    page_title="Nginx - Reverse Proxy & Sécurité",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- STYLE ---
st.markdown(
    """
    <style>
    .main-header {font-size: 2.5rem; font-weight: bold; color: #1f77b4; margin-bottom: 1rem;}
    .sub-header {font-size: 1.5rem; font-weight: 600; color: #2c3e50; margin-top: 2rem;}
    .value-card {background-color: #f8f9fa; padding: 1.5rem; border-radius: 8px; border-left: 5px solid #009639; height: 100%;}
    </style>
    """,
    unsafe_allow_html=True,
)

# --- EN-TÊTE ---
st.markdown(
    '<p class="main-header">Nginx : La façade du projet</p>', unsafe_allow_html=True
)
st.markdown("""
Aucun des services applicatifs (**Streamlit**, **BentoML**) n'est exposé directement sur Internet.
**Nginx** agit comme unique point d'entrée public de la stack : il termine le HTTPS, route les requêtes
vers le bon service interne et protège l'API contre les abus.
""")

st.divider()

# --- SECTION 1 : ROLE DE REVERSE PROXY ---
st.markdown(
    '<p class="sub-header">1. Reverse Proxy : un point d\'entrée unique</p>',
    unsafe_allow_html=True,
)

col_role, col_diag = st.columns([1, 1])

with col_role:
    st.markdown("""
    Tout le trafic externe passe par le conteneur `nginx`, seul service dont les ports `80` et `443` sont
    publiés sur l'hôte. En interne, il redirige vers les bons conteneurs Docker via le réseau privé :

    | Route | Destination | Rôle |
    | :--- | :--- | :--- |
    | `/` | `streamlit:8501` | Interface utilisateur de démonstration |
    | `/predict` | `ml-api:3000` | Endpoint de prédiction BentoML |

    **Avantage :** les conteneurs `streamlit` et `ml-api` n'ont besoin d'aucun port publié — ils restent
    injoignables depuis l'extérieur du réseau Docker.
    """)

with col_diag:
    st.graphviz_chart("""
    digraph Flux {
        rankdir=LR;
        node [shape=box, style=filled, fontname="Arial", penwidth=2];
        edge [fontsize=10, color="#555"];

        Client [label=" Client\\n(navigateur)", fillcolor="#2c3e50", fontcolor="white"];

        subgraph cluster_nginx {
            label="Conteneur Nginx (80 / 443)";
            style=dashed;
            color=gray;
            Nginx [label=" Nginx\\nReverse Proxy HTTPS", fillcolor="#009639", fontcolor="white"];
        }

        Streamlit [label=" Streamlit\\n(port 8501, interne)", fillcolor="#ff4b4b", fontcolor="white"];
        BentoML [label=" BentoML\\n/predict (port 3000, interne)", fillcolor="#f1c232"];

        Client -> Nginx [label="HTTPS 443"];
        Nginx -> Streamlit [label="location /"];
        Nginx -> BentoML [label="location /predict"];
    }
    """)

st.divider()

# --- SECTION 2 : TERMINAISON TLS & SECURITE ---
st.markdown(
    '<p class="sub-header">2. Terminaison HTTPS & en-têtes de sécurité</p>',
    unsafe_allow_html=True,
)

col_tls, col_headers = st.columns([1, 1])

with col_tls:
    st.markdown("""
    ### Chiffrement TLS
    Nginx termine le HTTPS : il présente le certificat au client et dialogue ensuite en clair avec les
    services internes, à l'intérieur du réseau Docker.

    - Le port `80` (HTTP) ne fait qu'une chose : **rediriger en 301 vers le `443`**.
    - Seuls les protocoles **TLSv1.2** et **TLSv1.3** sont acceptés.
    - Les certificats sont générés localement (`nginx.crt` / `nginx.key`) et montés dans l'image via le
      `Dockerfile` du service.
    """)
    st.code(
        """server {
    listen 80;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    ssl_certificate     /etc/nginx/certs/nginx.crt;
    ssl_certificate_key /etc/nginx/certs/nginx.key;
    ssl_protocols       TLSv1.2 TLSv1.3;
}""",
        language="nginx",
    )

with col_headers:
    st.markdown("""
    ### En-têtes de sécurité
    Chaque réponse HTTPS embarque un jeu d'en-têtes qui durcit le comportement du navigateur :
    """)
    security_headers = [
        {
            "En-tête": "Strict-Transport-Security",
            "Effet": "Force le HTTPS pour 1 an (anti-downgrade)",
        },
        {
            "En-tête": "X-Frame-Options",
            "Effet": "Interdit l'affichage du site dans une iframe tierce (anti-clickjacking)",
        },
        {
            "En-tête": "X-Content-Type-Options",
            "Effet": "Empêche le navigateur de deviner un type MIME (nosniff)",
        },
        {
            "En-tête": "X-XSS-Protection",
            "Effet": "Active la protection XSS historique du navigateur",
        },
        {
            "En-tête": "Referrer-Policy",
            "Effet": "Limite les informations envoyées lors d'un changement de page",
        },
    ]
    st.dataframe(security_headers, use_container_width=True, hide_index=True)

st.divider()

# --- SECTION 3 : PROTECTION CONTRE LES ABUS ---
st.markdown(
    '<p class="sub-header">3. Limitation de débit (rate limiting)</p>',
    unsafe_allow_html=True,
)
st.markdown("""
Deux zones de limitation indépendantes protègent respectivement l'interface Streamlit et l'API de prédiction
contre un usage abusif ou un pic de trafic imprévu.
""")

st.code(
    """limit_req_zone $binary_remote_addr zone=streamlit_limit:10m rate=50r/s;
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=50r/s;

location /predict {
    limit_req zone=api_limit burst=200 nodelay;
    limit_req_status 429;
    proxy_pass http://ml_api/predict;
}""",
    language="nginx",
)

st.info("""
 **Lecture de la règle :** chaque adresse IP est limitée à **50 requêtes/seconde** en régime permanent, avec
une tolérance de **200 requêtes en rafale** (`burst`) traitées sans délai (`nodelay`). Au-delà, Nginx répond
directement `429 Too Many Requests` sans même solliciter Streamlit ou BentoML.
""")

st.divider()

# --- CONCLUSION ---
st.success("""
 **Synthèse :**
Nginx protège la stack en réduisant sa surface d'exposition à un unique point d'entrée chiffré. Il assure
deux rôles complémentaires : **routage** (vers Streamlit et BentoML) et **sécurité** (TLS, en-têtes HTTP,
rate limiting anti-abus).
""")
