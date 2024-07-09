import streamlit as st
import pandas as pd
import numpy as np

title = "MLOPS Project Accident Predictions May 24"
subtitle = "GreenLightServices"
sidebar_name = "Introduction"


def run():

    st.title(title)
    st.subheader(subtitle)
    st.markdown("---")

    st.markdown(
        """
        ### Project Description
        In this project we intend to demonstrate our core MLOps approaches, processes and tools.
        
       We used a pre-existing model, prioritizing the MLOps aspect of deploying a service based on an ML model 
       rather than enhancing the model's performance. 
        
        The core components of this service are:
       
        - **Service Platform** to provide the service based on a Docker environment
        - **Secured API** using user authentication and authorisation to predict
        - **User Interface** for Predictions with streamlit using the /predict- endpoint
        - **Supervised Folders** for new data intake
        - **Automated Training** integrating new data via Airflow
        - **Automated Model Evaluation** to ensure good performance via MLFlow
        - **Automated CI/CD processes** to maintain software quality in Github Actions and Docker Hub
        - **Future Developements** if we had additional time
    
        """
        
    )


# This Streamlit app is designed to interactively present various aspects of our project. Navigate through the following sections:
# Each tab is dedicated to a specific aspect of the project, offering insights and allowing for interactive engagement with the project's outputs.
