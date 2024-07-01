from collections import OrderedDict

import streamlit as st
from PIL import Image
import config


from tabs import predictions, intro, service, bugs

st.set_page_config(
    page_title=config.TITLE
    # page_icon="assets/model.png",
)

with open("src/green_light_ui/style.css", "r") as f:
    style = f.read()

st.markdown(f"<style>{style}</style>", unsafe_allow_html=True)


TABS = {}

TABS = OrderedDict(
    [
        (intro.sidebar_name, intro),
        (predictions.sidebar_name, predictions),
        (service.sidebar_name, service),
        (bugs.sidebar_name, bugs),
    ]
)


def run():

    image = Image.open("./src/green_light_ui/assets/GreenLights.png")
    st.sidebar.image(
        image,
        width=200,
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
