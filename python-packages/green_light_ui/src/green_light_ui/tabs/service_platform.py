import streamlit as st
import pandas as pd
import numpy as np



# File locations in Docker
streamlit_base = '/app/src/green_light_ui'

# Page settings

title = "GreenLightServices - Service Platform"
sidebar_name = "Service Platform"



def run():

    st.title(title)

    st.markdown("## Description of the GreenLightServices Platform ")
    st.image(streamlit_base + "/assets/ServicePlatform.png")