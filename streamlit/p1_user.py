import streamlit as st
import requests
import time
import json

# Definition des chemins, url et noms 
api_url_heroku = "https://dst-mar-accident-ee3901cfb695.herokuapp.com"
api_url_local = "http://localhost:8000"  # A verifier
api_url = api_url_heroku

# features utilisées par default (predict = 0)
features_0= {'place':1,
                            'catu':3,
                            'sexe':2,
                            'secu1':0.0,
                            'year_acc':2021,
                            'victim_age':19.0,
                            'catv':2.0,
                            'obsm':1.0,
                            'motor':1.0,
                            'catr':4,
                            'circ':2.0,
                            'surf':1.0,
                            'situ':1.0,
                            'vma':30.0,
                            'jour':4,
                            'mois':11,
                            'lum':5,
                            'dep':59,
                            'com':59350,
                            'agg_':2,
                            'int':2,
                            'atm':0.0,
                            'col':6.0,
                            'lat':50.6325934047,
                            'long':3.0522062542,
                            'hour':22,
                            'nb_victim':4,
                            'nb_vehicules':1
                        }


###  LES FONCTIONS  ####################################################

# Barre de progression
def progress_bar():
        progress_text = "En attente de la réponse de l'API"
        my_bar = st.progress(0, text=progress_text)

        for percent_complete in range(100):
            time.sleep(0.001)
            my_bar.progress(percent_complete + 1, text=progress_text)
        time.sleep(1)
        my_bar.empty()

# Testet l'API
def check_api():
    try:
        url = f"{api_url}/status"
        headers = {'accept': 'application/json'}    # inutile ?
        response = requests.get(url, headers=headers)
        progress_bar()
        if response.status_code == 200:
            result = response.json()
            st.write(result)
            st.success("L'API est accessible et fonctionne correctement.", icon="✅")        
        else:
            st.write(f"""Erreur lors de la vérification de l'API.  
                     Code de statut : {response.status_code}""")

    except requests.exceptions.RequestException as e:
        return f"Erreur lors de la requête GET : {str(e)}"

# Effectuer une prédiction
@st.cache_data
def predict_api(features):
    url = f"{api_url}/prediction"
    response = requests.post(url, json=features, 
                            auth = ('admin1', 'admin1'))
    if response.status_code == 200:
        result = response.json()
        if result["prediction"] == 0:
            st.success("Estimation : **Pas de blessé grave**")
        else:
            st.error("Estimation : **Accident GRAVE**") 

    else:
        st.write(response.status_code)
        st.write(response.json())
        st.write (f"Erreur d'API lors de la prediction. Code de statut : {response.status_code}")
        st.write (f"Erreur d'API lors de la prediction. Code de statut : {response.text}")


###  CONTENU DE LA PAGE  #######################################################################

def app():

    # Faire une prediction 
    st.write("# Interface Utilisateur")
    st.write("### Réaliser une prédiction:")

    col1, col2, col3, col4, col5, col6 = st.columns(6,gap = 'large')
    def_value = features_0
    keys_list = list(features_0.keys())

    user_values = {}

    for i in range(5):
        key = keys_list[i]
        user_values[key] = col1.number_input(key, value=def_value[key])
    for i in range(5):
        key = keys_list[i+5]
        user_values[key] = col2.number_input(key, value=def_value[key])
    for i in range(5):
        key = keys_list[i+10]
        user_values[key] = col3.number_input(key, value=def_value[key])
    for i in range(5):
        key = keys_list[i+15]
        user_values[key] = col4.number_input(key, value=def_value[key])
    for i in range(4):
        key = keys_list[i+20]
        user_values[key] = col5.number_input(key, value=def_value[key])
    for i in range(4):
        key = keys_list[i+24]
        user_values[key] = col6.number_input(key, value=def_value[key])
    
    st.write(" ")
    st.write(" ")
    col1, col2 = st.columns([0.65,0.35], gap = 'medium')
    with col1:
        predict_api(user_values) 
    col2.write("Pour tester un accident grave, changer: catu = 3 et catr = 1 (pieton sur autoroute !!)")

    st.markdown("---")  
    if st.button("Test de la connexion"):
        check_api()

# TODO:
# Nettoyer progressbar (inutiles car synchrones ?)


