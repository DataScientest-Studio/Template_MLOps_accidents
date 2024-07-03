from pathlib import Path
from collections import OrderedDict

import streamlit as st
from PIL import Image
import config


from tabs import intro, user_interface, service_platform, api, updates, training, evaluation, ci_cd, monitoring


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
    run()
