import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

green_light_ui_base = Path(__file__).parent.parent


title = "Model Training"
subtitle = " Training the model on the event of new data"
sidebar_name = "Model Training"


def run():

    st.title(title)
    st.subheader(subtitle)
    with st.expander(
        "**Model Training is managed by an Airflow DAG that watches two conditions: *new data* and *model existence***"
    ):
        st.write(
            """
        Model Training is managed by an Airflow DAG. The Airflow components are initiated at system startup. See  Tab *Service Platform*for an overview of all components. 

        There are two situations, when the DAG fires: 
        * There is no model at all in the folder `/models` inside the docker container. 
        * New data arrived and need to be incorporated

        The Model Training and Evaluation pipeline relies on a specific file structure in the Docker Volumes 
        
            Volumes
                airflow -> contains the Airflow logs etc
                data
                    metrics -> metrics written in the DAG
                    mlflow -> model performance logged during evaluation. See tab *Model Evaluation* for details
                    predictions -> predictions logged for archiving purposes
                    preprocessed
                        archived -> previous data 
                        X_train.csv -> current data from preprocessing the actual data in the PG DB
                        X_test.csv  -> current data from preprocessing the actual data in the PG DB
                        y_train.csv -> current data from preprocessing the actual data in the PG DB
                        y_test.csv  -> current data from preprocessing the actual data in the PG DB
                db
                db_admin
                models
                  archive -> Folder with previous models. The current model is moved here with a time stamp after a new model was validated 
                  new -> Folder with new model, directly after training. Will be moved to `/models` after successful validation
                  trainied_model.joblob -> the current model
    """
        )

    with st.expander(
        "**The DAG has two branches and performs several steps in a productive branch to train and validate the model**"
    ):

        st.image(str(green_light_ui_base / "assets" / "training_dag.png"))

        st.write(
            """
        * `initiate` checks if the model is missing and if there are new data. In either case the DAG initiates the training. 
        * To check for new data, an Airflow variable is checked to exist. This variable is set from the data ingestion DAG. If the variable was found, a training run will be initiated and the varible is deleted
        * `data_transformation` retrieves the data from the postgress database. The PG DB has the four base files from the french authorities incl. the new data.
        The tasks transforms the base files into the `X_train`, `X_test`, `y_train`, and `y_test` files according the scripts we inherited with project initiation. 
        * `model_training` takes the data and trains an `xgboost` classifier. We changed this classifier with respect to the `RandomForestClassiifer` in the original scripts, 
        because the standard Shaply-Reports from MLflow don't take the RFC well. The newly trained model is written in a folder /new in the /models volume inside 
        the Docker container for later validation. 
        * `model_metrics` just writes  current metrics to file for later inspection: \n 
                {
                "acc": 0.7793418647166362,
                "f1-score": 0.6582995187317167,
                "mse": 0.2206581352833638,
                "r2": 0.02446833865035314
                }
        * `validate_push` is a branch that uses a call to `mlflow.evaluate()` in order to validate the model against predefined validation criteria.
        * If the model was successfully validated, `push_production` moves the current model to a folder `/archive` with a time stamp on it and moves the new model to `/models`
        as the new current model. Model evaluation is discussed in detail in tab __Model Evaluation__
        * `refresh_api` calls the `refresh` endpoint of our API to trigger a reload of the model, thus concluding the training cycle. 
        * in case the validation fails, nothing changes. The current model stays put. MISSING FEATURE: We did not implement an email alert yet to inform the sysadmins 
        an a failed DAG
        * If there are no new data and the model exists, nothing happens and after 5 minutes, the DAG looks again
        
        """
        )

    st.write(
        """
        Check [here](http://localhost:8080) to see the Airflow interface with the current DAG waiting for actions

        Check [here](https://github.com/DataScientest-Studio/may24_bmlops_accidents/blob/master/airflow/dags/1_training_pipeline_dag.py) to see the code of the DAG
    """
    )
