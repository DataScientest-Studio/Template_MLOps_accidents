import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
import time


title = "Make a Prediction"
sidebar_name = "predictions"

## Definitions
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
    "atm": 0,
    "col": 6,
    "lat": 48.60,
    "long": 2.89,
    "hour": 17,
    "nb_victim": 2,
    "nb_vehicules": 1,
}


def input_feature(feature):
    st.write(f"**'{feature}'**, current value: {features[feature]}")
    value = st.number_input(feature)
    return value


## run the page
def run():
    # settings

    st.title(title)

    st.markdown(
        """
        **Make a prediction:** 
        To make a prediction, enter the values for the features in the boxes below. Then click the button _Make Prediction_ below. The prediction will be displayed in the box with title 'Prediction'.
        
        To make a new prediction with completely new data, click the button _Make New Prediction_ below. This will erase all data entered in the boxes. 
        
        You now can enter new values for the features. All boxes must be filled before you can make a new prediction.
        """
    )

    new_features = {}

    dict_features = list(features.items())
    len_features = len(dict_features) // 3 + 1

    if st.button("Make New Prediction"):
        st.text("New Prediction")

    if st.button("Make Prediction"):
        st.text("Prediction")
    st.write("___")
    col1, col2, col3 = st.columns(3)
    with col1:

        new_features["place"] = input_feature("place")
        new_features["catu"] = input_feature("catu")
        new_features["sexe"] = input_feature("sexe")
        new_features["secu1"] = input_feature("secu1")
        new_features["year_acc"] = input_feature("year_acc")
        new_features["victim_age"] = input_feature("victim_age")
        new_features["catv"] = input_feature("catv")
        new_features["obsm"] = input_feature("obsm")
        new_features["motor"] = input_feature("motor")

    with col2:

        new_features["catr"] = input_feature("catr")
        new_features["circ"] = input_feature("circ")
        new_features["surf"] = input_feature("surf")
        new_features["situ"] = input_feature("situ")
        new_features["vma"] = input_feature("vma")
        new_features["jour"] = input_feature("jour")
        new_features["mois"] = input_feature("mois")
        new_features["lum"] = input_feature("lum")
        new_features["dep"] = input_feature("dep")
        new_features["com"] = input_feature("com")
    with col3:
        new_features["agg_"] = input_feature("agg_")
        new_features["int"] = input_feature("int")
        new_features["atm"] = input_feature("atm")
        new_features["col"] = input_feature("col")
        new_features["lat"] = input_feature("lat")
        new_features["long"] = input_feature("long")
        new_features["hour"] = input_feature("hour")
        new_features["nb_victim"] = input_feature("nb_victim")
        new_features["nb_vehicules"] = input_feature("nb_vehicules")
