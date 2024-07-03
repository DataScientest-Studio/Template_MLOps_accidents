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

    st.markdown("## Description of the GreenLightServices Platform ")
    st.image(str(green_light_ui_base / "assets" / "ServicePlatform.png"))