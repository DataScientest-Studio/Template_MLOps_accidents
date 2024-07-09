import streamlit as st
import pandas as pd
import numpy as np

title = "Model Evaluation using MLFlow"
sidebar_name = "Model Evaluation"


def run():

    st.title(title)
    with st.expander(
        "**Model evaluation is done using MLflow technology outside the Docker environment on the local maching that is running Docker**"
    ):
        st.write(
            """
        Model evaluation is done using MLflow technology. 
        * We set up MLFlow as a non dockerized application on the local machine running the docker environment, mainly to avoid the complexity of implementing and testing
        another heavy weight dockerized application together with what we aldeady had. 
        * The `MetricThreshold` class is used to define thresholds for performance metrics of the model. 
        * We then use the `mlflow.evaluate()` method the evaluate the freshly trained model against the defined thresholds
        * If the evaluation is successful, the new model is accepted and pushed to production in a laster step
    
        """
        )
    with st.expander("**Model performance can be visualized utilizing the MLflow UI**"):
        st.write(
            """
        * During model evaluation the MLflow methods log metrics and artifacts in specific folders
          * /Volumes/data/mlflow/mlruns
          * /Volumes/data/mlflow/mlarfifacts
        * The performance of trainings run sofar can thus be inspected
        * We used the `mlflow.evaluate()` standard settings and artifacts for the model type `classifier`. 
        * Check the MLflow UI [here](http://localhost:5000)
        * Check the model_evaluation code [here](https://github.com/DataScientest-Studio/may24_bmlops_accidents/blob/master/airflow/dags/model_evaluation.py)
"""
        )
