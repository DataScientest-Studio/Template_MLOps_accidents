import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

# Root dir of the green light ui project
green_light_ui_base = Path(__file__).parent.parent


title = "Secured API with unit testing"
sidebar_name = "API"


def run():

    st.title(title)

    st.markdown(
        """
        <style>
        .streamlit-expanderHeader p {
            font-size: 20px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.expander(
        "**The API is based on FastAPI. Authentication uses the HTTPBearer, HTTPAuthorizationCredentials classes/methods**"
    ):
        st.image(str(green_light_ui_base / "assets" / "API.png"))
        st.write(
            """
    * We implemented a FastAPI with several endpoints
      * `/` 
      * `/user/login`
      * `/user/signup`
      * `/refresh`
      * `/predict`
    * The authentization scheme asks for a username and password. After testing for existence, a token with defined lifetime is returned from the API
    * The token is needed to access any other endpoint, except `/` 
    * After expiry of the token, the  user needs to login again.
    * The token lifetime is set to 6000 secs
    * The API gets tested in the development phase against a test script using pytest. It also gets tested after pushing in master by means of GitHub Actions 

            """
        )

    with st.expander("**Take a look at the API in action using FastAPI /docs**"):
        st.write("Check out this [link](http://localhost:8001/docs)")

    with st.expander("**Take a look at the code in the GitHub**"):

        st.write(
            "Link to API [link](https://github.com/DataScientest-Studio/may24_bmlops_accidents/blob/master/python-packages/model_api/src/model_api/api.py)"
        )
    with st.expander(
        "**Take a look at the GitHub actions testing the API on push against master**"
    ):

        st.write(
            "Link to GitHub Actions testing the API [link](https://github.com/DataScientest-Studio/may24_bmlops_accidents/blob/2dc72e54da7e0bc3ba113eca3f884179af56af54/.github/workflows/python-app.yml#L41)"
        )
