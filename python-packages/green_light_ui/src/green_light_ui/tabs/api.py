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
        "**We used JSON Web Token (JWT)-Bearer authentication and authorization from FastAPI**"
    ):
        st.image(str(green_light_ui_base / "assets" / "API.png"))
        st.write(
            """
    * We implemented a FastAPI with the following endpoints
      * `/`
      * `/user/login`
      * `/user/signup`
      * `/refresh`
      * `/predict`
    * Authentication requires a username and password. 
    * Admin credentials (ADMIN_USERNAME, ADMIN_PASSWORD) are defined in the ./.env file.
    * When veryfiying as admin or signed-up user, the API issues a JWT Bearer access token.
    * The /predict and /refresh endpoints demand authorization with this access token.
    * The token issued has a lifetime of 6000 seconds (100 minutes).
    * Once it has expired, users must obtain a new token to continue on the protected endpoints.
    * During development, the API is tested using pytest scripts.
    * Additionally, after every push to the master branch, the application undergoes automated testing with GitHub Actions.
    
            """
        )

    with st.expander("**Take a look at the API in action using FastAPI /docs**"):
        st.write("Check out this [link](http://localhost:8001/docs)")

    with st.expander("**Take a look at the code in GitHub**"):

        st.write(
            "Link to API [link](https://github.com/DataScientest-Studio/may24_bmlops_accidents/blob/master/python-packages/model_api/src/model_api/api.py)"
        )
    with st.expander(
        "**Take a look at the GitHub actions testing the API on push against master**"
    ):

        st.write(
            "Link to GitHub Actions testing the API [link](https://github.com/DataScientest-Studio/may24_bmlops_accidents/blob/2dc72e54da7e0bc3ba113eca3f884179af56af54/.github/workflows/python-app.yml#L57)"
        )
