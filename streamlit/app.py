import streamlit as st
import requests
import time
import json

# Lien vers les pages
import p1_user
import p2_admin

# Peut être desactivée (commentaire) pour présentation "etroite"
st.set_page_config(layout="wide")  

# Definition des chemins, url et noms 
logo_path = "images/dessin2.jpg"

api_url_heroku = "https://dst-mar-accident-ee3901cfb695.herokuapp.com"
api_url_local = "http://localhost:8000"  # A verifier
api_url = api_url_local




###  Barre laterale commune  #####################################################

st.sidebar.title("Aide à l’évaluation de gravité d’un accident")
st.sidebar.image(logo_path, width=150, use_column_width="auto" )
st.sidebar.write("""
                #### Solution d’assistance pour les centre d’appel des secours
                """)

# Sommaire
PAGES = {"Utilisateur":p1_user, "Admin": p2_admin}
selection = st.sidebar.radio("", options=list(PAGES.keys()))
page = PAGES[selection]
page.app()


st.sidebar.write(' ')
st.sidebar.write(' ')
st.sidebar.write(' ')
st.sidebar.write(' ')

# Credits
st.sidebar.write("""
                **Projet Accidents**  
                MLOps oct24  
                 
                **Auteurs :**  
                QUESSON Cyrille   
                BETROUNI Elkhalil   
                BOINALI Nadjedine  
                CALMETTES Ludovic  
                **Mentor:**  
                Maria DOMENZAIN ACEVEDO            
                 """)

