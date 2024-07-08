from pathlib import Path
from collections import OrderedDict

import streamlit as st
from PIL import Image
import config
import requests


from tabs import (
    intro,
    user_interface,
    service_platform,
    api,
    updates,
    training,
    evaluation,
    ci_cd,
    monitoring,
)


DOCKERIZED = True

# Handle login prerequisites

if DOCKERIZED:
    api_url = "http://model_api_from_compose:8000/user/login"
else:
    api_url = "http://localhost:8001/user/login/"

# Initialization

if "token" not in st.session_state:
    st.session_state["token"] = "0"

# File locatements in Docker
app_script_base = Path(__file__).parent


st.set_page_config(
    page_title=config.TITLE
    # page_icon="assets/model.png",
)

with open(app_script_base / "style.css", "r") as f:
    style = f.read()

st.markdown(f"<style>{style}</style>", unsafe_allow_html=True)


TABS = {}

TABS = OrderedDict(
    [
        (intro.sidebar_name, intro),
        (service_platform.sidebar_name, service_platform),
        (api.sidebar_name, api),
        (user_interface.sidebar_name, user_interface),
        (updates.sidebar_name, updates),
        (training.sidebar_name, training),
        (evaluation.sidebar_name, evaluation),
        (ci_cd.sidebar_name, ci_cd),
        (monitoring.sidebar_name, monitoring),
    ]
)


def get_login(username, password):
    if DOCKERIZED:
        url = "http://model_api_from_compose:8000/user/login"
    else:
        url = "http://localhost:8001/user/login"

    response = requests.post(url, json={"username": username, "password": password})
    token = response.json()["access_token"]
    print("token = ", token)
    return token


def token_valid(token):
    if DOCKERIZED:
        url = "http://model_api_from_compose:8000/secured"
    else:
        url = "http://localhost:8001/secured"

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers).json()
    # print("response = ", response)
    try:
        if response["message"] == "Hello World! but secured":
            return True
    except KeyError:
        print("response = ", KeyError)
        return False


def run():

    image = Image.open(app_script_base / "assets/GreenLights.png")
    st.sidebar.image(
        image,
        width=100,
    )

    tab_name = st.sidebar.radio("Choose Tab", list(TABS.keys()), 0)
    st.sidebar.markdown("---")

    # if tab_name != "catalogue":

    st.sidebar.markdown(f"## {config.PROMOTION}")

    st.sidebar.markdown("### Team members:")
    for member in config.TEAM_MEMBERS:
        st.sidebar.markdown(member.sidebar_markdown(), unsafe_allow_html=True)

    tab = TABS[tab_name]
    tab.run()


if __name__ == "__main__":

    if not token_valid(st.session_state.token):
        username = st.text_input(label="username", value="admin")
        password = st.text_input(label="password", value="adm1n")
        if st.button(label="Login"):
            token = get_login(username, password)
            st.session_state.token = token
    # print(st.session_state.token)
    if token_valid(st.session_state.token):
        run()
