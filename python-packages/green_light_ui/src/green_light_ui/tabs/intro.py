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
        In this project we intend to demonstrate core MLOPS approaches, processes and tools.
        
        We demonstrate this by using a given model, treating 
        the datascience part as solved,  focusing on the MLOPS part of providing a service based on an ML-Model. 
        
        As scenario we use a hypothetical service provider 'GreenLightService' that offers the service of predicting 
        the gravity of an accident in France. 
        
        The core components of this service are:
       
        - **Service Platform** to provide the service based on a Docker environment
        - **Secured API** with unit testing
        - **User Interface** to make predictions based on the ML Model
        - **Supervised Folders for Data Intake** to catch new data coming in 
        - **Automated Training** of the model to include the new data in the predictions
        - **Automated Model Evaluation** to ensure performance of the model
        - **Automated CI/CD processes** to ensure consistent development quality of software components
        - **Service Monitoring** to monitor the service availability
        ...
        """
        
    )


# This Streamlit app is designed to interactively present various aspects of our project. Navigate through the following sections:
# Each tab is dedicated to a specific aspect of the project, offering insights and allowing for interactive engagement with the project's outputs.
