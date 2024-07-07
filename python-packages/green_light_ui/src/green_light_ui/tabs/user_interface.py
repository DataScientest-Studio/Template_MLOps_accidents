import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
import time
from pydantic import BaseModel
import requests
import json
import os

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# URLs
url_prediction = "http://model_api_from_compose:8000/predict"
# url_prediction = "http://localhost:8001/predict"


## Definitions

# Stuff for the UI-Layout to input the features

features = {
    "place": 10,
    "catu": 3,
    "sexe": 1,
    "secu1": 0.0,
    "year_acc": 2021,
    "victim_age": 60,
    "catv": 2,
    "obsm": 1,
    "motor": 1,
    "catr": 3,
    "circ": 2,
    "surf": 1,
    "situ": 1,
    "vma": 50,
    "jour": 7,
    "mois": 12,
    "lum": 5,
    "dep": 77,
    "com": 77317,
    "agg_": 2,
    "int": 1,
    "atm": 1,
    "col": 6,
    "lat": 48.60,
    "long": 2.89,
    "hour": 17,
    "nb_victim": 2,
    "nb_vehicules": 1,
}

feature_en = {
    "place": "Seat occupied",
    "catu": "User category",
    "sexe": "Gender",
    "secu1": "Safety equipment",  #
    "year_acc": "Year",
    "victim_age": "Age of victim",  #
    "catv": "Vehicle category",
    "obsm": "Mobile obstacle hit",
    "motor": "Type of  engine",
    "catr": "Road category ",  #
    "circ": "Traffic regime",
    "surf": "Surface condition",
    "situ": "Accident situation",
    "vma": "Max allowed speed",
    "jour": "Day",
    "mois": "Month",
    "lum": "Light Conditions",
    "dep": "Department",
    "com": "Community ",
    "agg_": "Rural/Urban",
    "int": "Intersection",
    "atm": "Atmosph. conditions",
    "col": "Type of collision",  #
    "lat": "Latitude",  #
    "long": "Longitude",  #
    "hour": "Hour",
    "nb_victim": "Number of victims",
    "nb_vehicules": "Number of vehicles",
}

# here we define the number of core features we want to present for prediction
# comment out the ones you don't want
core_features = {
    # "place": 10,
    # "catu": 3,
    # "sexe": 1,
    "secu1": 0.0,
    # "year_acc": 2021,
    "victim_age": 60,
    "catv": 2,
    # "obsm": 1,
    # "motor": 1,
    "catr": 3,
    # "circ": 2,
    # "surf": 1,
    # "situ": 1,
    "vma": 50,
    "jour": 7,
    "mois": 12,
    # "lum": 5,
    # "dep": 77,
    # "com": 77317,
    # "agg_": 2,
    # "int": 1,
    # "atm": 1,
    "col": 6,
    # "lat": 48.60,
    # "long": 2.89,
    "hour": 17,
    # "nb_victim": 2,
    # "nb_vehicules": 1,
}


def get_jwt_token():
    # url = "http://localhost:8001/user/login"
    url = "http://model_api_from_compose:8000/user/login"
    response = requests.post(
        url, json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
    )
    token = response.json()["access_token"]
    print("token = ", token)
    return token


def check_inputs(new_features):
    for feature in new_features:
        if new_features[feature] == None:
            return False
    return True


def get_prediction(new_features):

    token = get_jwt_token()
    # headers = {"accept": "application/json", "Authorization": f'Bearer {token}'  }
    headers = {"Authorization": f"Bearer {token}"}
    prediction = requests.post(
        url_prediction, data=json.dumps(new_features), headers=headers
    )

    prediction = prediction.json()["prediction"][0]
    print("prediction", prediction)
    print("new_features", new_features)
    return prediction


#   -H 'accept: application/json' \
#   -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiYWRtaW4iLCJleHBpcmVzIjoxNzIwMTc3NTY2Ljk2OTc4NzR9.lybhCD3TsUb5i3oftS4dxH868ahYN0UL9vbDVP3edRU' \
#   -H 'Content-Type: application/json' \


def input_feature(feature):
    """
    input a feature and return its value
    this is required to build the three input columns with flexible number of rows
    depending on the number of core features
    """

    st.write(f"**'{feature_en[feature]}'**, Default: {features[feature]}")
    value = st.number_input(
        feature_en[feature], label_visibility="collapsed", value=new_features[feature]
    )
    # value = st.selectbox(feature_en[feature], options = options, label_visibility="collapsed", index = idx)
    return value


# default the new features to the default features in order to have a feasible start configuration
new_features = {}
for key, value in features.items():
    new_features[key] = value

# Page settings
title = "GreenLightServices"
subtitle = " Custom UI to make a prediction"
sidebar_name = "User Interface"


## run the page
def run():
    # settings
    global new_features
    global features

    st.title(title)
    st.subheader(subtitle)

    st.markdown(
        """
        **Make a prediction:** 
        To make a prediction, enter the values for the features in the boxes below. Then click the button _Make Prediction_ below. The prediction will be displayed in the box with title 'Prediction'.
        
        To make a new prediction with completely new data, click the button _Make New Prediction_ below. This will erase all data entered in the boxes. 
        
        You now can enter new values for the features. All boxes must be filled before you can make a new prediction.
        """
    )
    # number of rows of features when we distribute over 3 cols
    num_core_features = len(core_features)
    num_rows = (
        num_core_features // 3
        if num_core_features % 3 == 0
        else num_core_features // 3 + 1
    )

    st.write("___")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Use Default"):
            for key, value in features.items():
                new_features[key] = value
        st.write("Default:")
    with col2:
        if st.button("Make Prediction"):
            if check_inputs(new_features):
                # prediction = get_prediction(new_features)
                prediction = get_prediction(features)
                # prediction = get_jwt_token()
                st.write(f"Prediction: {prediction}")
            else:
                st.write("Please fill all the boxes before making a prediction")

    with col3:
        if st.button("Reset"):
            for key, value in core_features.items():
                new_features[key] = None

    st.write("___")
    col4, col5, col6 = st.columns(3)
    with col4:
        col = 0
        idx = 0
        for key, value in core_features.items():
            if (idx >= col * num_rows) & (idx < (col + 1) * num_rows):
                # print(idx)
                new_features[key] = input_feature(key)
            idx += 1

            if idx == (col + 1) * num_rows:
                break
        # print(key)

    with col5:
        col = 1
        idx = 0
        for key, value in core_features.items():
            if (idx >= col * num_rows) & (idx < (col + 1) * num_rows):
                # print(idx)
                new_features[key] = input_feature(key)
            idx += 1
            if idx == (col + 1) * num_rows:
                break

    with col6:
        col = 2
        idx = 0
        for key, value in core_features.items():
            if (idx >= col * num_rows) & (idx < (col + 1) * num_rows):
                new_features[key] = input_feature(key)
            idx += 1
            if idx == (col + 1) * num_rows:
                break
    st.write("___")
    st.subheader("Technical Details to the UI")
    with st.expander("**This UI was build using the Streamlit package**"):
        st.write(
            """
        We used the streamlit package to build a very simple customer UI. 
        * The actual customer page is **this** page. Here you can make the prediction, which is currently the only service we offer
        * All other pages serve to demonstrate the project
        * This page was put behind a very rudimentarty securization using the JTW-Bearer from the FastAPI. 
        * Checkout the code [here]:(https://github.com/DataScientest-Studio/may24_bmlops_accidents/tree/master/python-packages/green_light_ui/src/green_light_ui)
  
        """
        )
