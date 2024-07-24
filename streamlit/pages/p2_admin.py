import streamlit as st
import requests

# Definition des chemins, url et noms 
from streamlit.pages.p1_user import api_url


###  LES FONCTIONS  ####################################################


def authenticate(username, password):
    valid_username = "admin1"
    valid_password = "admin1"

    if username == valid_username and password == valid_password:
        return True
    else:
        return False

def check_api2():
    try:
        url = f"{api_url}/status"
        headers = {'accept': 'application/json'}    # inutile ?
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            result = response.json()
            st.write(result)
            st.success("L'API est accessible et fonctionne correctement.", icon="✅")        
        else:
            return f"Erreur lors de la vérification de l'API. Code de statut : {response.status_code}"

    except requests.exceptions.RequestException as e:
        return f"Erreur lors de la requête GET : {str(e)}"

def new_user(name, password):
    """Permet d'ajouter un utilisateur /new_user - (name, password) """
    try:
        url = f"{api_url}/new_user"
        headers = {'accept': 'application/json'}    # inutile ?
        response = requests.post(
            url,
            headers=headers,
            json={"name": name, "password": password}, 
            auth = ('admin1', 'admin1')
        ) 
        if response.status_code == 200: 
            st.success("L'utilisateur a été créé", icon="✅")        
        else:
            st.error("Ce nom existe deja, choisissez en un autre")
        st.write(response.json())

    except requests.exceptions.RequestException as e:
        return f"Erreur lors de la requête POST : {str(e)}"

def new_admin(name, password):
    """Permet d'ajouter un admin /new_admin - (name, password) """
    try:
        url = f"{api_url}/new_admin"
        headers = {'accept': 'application/json'}    # inutile ?
        response = requests.post(
            url,
            headers=headers,
            json={"name": name, "password": password}, 
            auth = ('admin1', 'admin1')
        )     
        if response.status_code == 200: 
            st.success("L'admin et l'utilisateur ont été créés", icon="✅")        
        else:
            st.error("Ce nom existe deja, choisissez en un autre")
        st.write(response.json())

    except requests.exceptions.RequestException as e:
        return f"Erreur lors de la requête POST : {str(e)}"

def delete_user(name):
    try:
        url = f"{api_url}/delete_user/{name}"
        headers = {'accept': 'application/json'}    # inutile ?
        response = requests.delete(
            url,
            auth = ('admin1', 'admin1')
            )      
        if response.status_code == 200: 
            st.success("Utilisateur supprimé", icon="✅")        
        else:
            st.error("Problème: ")
        st.write(response.json())

    except requests.exceptions.RequestException as e:
        return f"Erreur lors de la requête POST : {str(e)}"

def delete_admin(name):
    try:
        url = f"{api_url}/delete_admin/{name}"
        headers = {'accept': 'application/json'}    # inutile ?
        response = requests.delete(
            url,
            auth = ('admin1', 'admin1')
            )      
        if response.status_code == 200: 
            st.success("Droits Admin supprimé", icon="✅")        
        else:
            st.error("Problème: ")
        st.write(response.json())

    except requests.exceptions.RequestException as e:
        return f"Erreur lors de la requête POST : {str(e)}"


def get_lists():
    try:
        url = f"{api_url}/test/users and admin list"
        response = requests.get(url)
        if response.status_code == 200:
            st.success("Listes récupérées.", icon="✅")        
        else:
            return f"Erreur lors de la vérification de l'API. Code de statut : {response.status_code}"
        st.write(response.json())

    except requests.exceptions.RequestException as e:
        return f"Erreur lors de la requête GET : {str(e)}"


###  CONTENU DE LA PAGE  #######################################################################

def app():  

    # Utilisation de la variable de session pour stocker l'état d'authentification
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    # Afficher le formulaire de connexion si l'utilisateur n'est pas authentifié
    if not st.session_state.authenticated:
        username = st.text_input("Nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password")

        if st.button("Se connecter"):
            if authenticate(username, password):
                st.session_state.authenticated = True
                st.success("Connexion réussie !")
            else:
                st.error("Nom d'utilisateur ou mot de passe incorrect.")
        if st.checkbox("aide developpeur"):
            st.write("nom: admin1, password: admin1")
    
    else:
        st.success("Vous êtes connecté !")

    if st.session_state.authenticated == True:
        with st.container():
            #-----------------
            st.write("# get Status")

            if st.button("check_api"):
                check_api2()  

            #-------------------
            st.write("# New User")
            with st.form("New User"):
                name = st.text_input("Name", key="name")
                password = st.text_input("Password", key="password", type="password")
                submit_button1 = st.form_submit_button("add")

            if submit_button1:
                new_user(name, password)

            #-------------------
            st.write("# New Admin")
            with st.form("New Admin"):
                name = st.text_input("Name")
                password = st.text_input("Password", type="password")
                submit_button2 = st.form_submit_button("add")

            if submit_button2:
                new_admin(name, password)
            
            #-------------------
            st.write("# Delete User")
            with st.form("Del User"):
                name = st.text_input("Name")
                submit_button3 = st.form_submit_button("del")

            if submit_button3:
                delete_user(name)

            #-------------------
            st.write("# Delete Admin")
            with st.form("Del Admin"):
                name = st.text_input("Name")
                submit_button4 = st.form_submit_button("del")

            if submit_button4:
                delete_admin(name)

            #-------------------
            st.write("# Users and Admins list")
            if st.button("Users and Admins list"):
                get_lists()
            


# TODO:
# Fenetre d'authentification doit disparaitre

            

        
        
                
            

        # Fonction pour l'authentification de l'utilisateur
        # def authenticate(username, password):
        #     valid_username = os.getenv("STREAMLIT_USERNAME")
        #     valid_password = os.getenv("STREAMLIT_PASSWORD")







