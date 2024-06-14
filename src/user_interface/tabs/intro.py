import streamlit as st
import pandas as pd
import numpy as np

title = "MLOPS Project Accident Predictions May 24"
sidebar_name = "Introduction"


def run():

    st.title(title)

    st.markdown("---")

    st.markdown(
        """
        ### Project Objective
        ...
        """
    )

    with st.expander("Read the Details"):
        st.markdown(
            """
        ### Problem Description 
   
        """
        )

    st.markdown(
        """
            ### Table of contents

            🗂️ **Make Predictions** \n
            🧠 **See Historical Data** \n
            📊 **Service Requests** \n
            🎯 **Report a Bug**\n
            ---




        """
    )


# This Streamlit app is designed to interactively present various aspects of our project. Navigate through the following sections:
# Each tab is dedicated to a specific aspect of the project, offering insights and allowing for interactive engagement with the project's outputs.
