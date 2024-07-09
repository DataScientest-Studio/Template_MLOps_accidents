from pathlib import Path

import streamlit as st
import pandas as pd
import numpy as np


# Root dir of the green light ui project
green_light_ui_base = Path(__file__).parent.parent

# Page settings

title = "GreenLightServices - Service Platform"
sidebar_name = "Service Platform"


def run():

    st.title(title)

    st.markdown("Description of the GreenLightServices Platform ")
    
    with st.expander(
        "**We implemented a hybrid architecture, with the customer service components on Docker and some MLOPS components in local infrastructure**"
    ):
        st.image(str(green_light_ui_base / "assets" / "Architecture_MVP.png"))
        
    with st.expander(
        "**We implemented a hybrid architecture, with the customer service components on Docker and some MLOPS components in local infrastructure**"
    ):
        st.image(str(green_light_ui_base / "assets" / "Architecture_final.png"))

    with st.expander(
        "**We can demonstrate some core MLOPS processes. However, limited time left some features for future development**"
    ):
        st.image(str(green_light_ui_base / "assets" / "SLC.png"))
