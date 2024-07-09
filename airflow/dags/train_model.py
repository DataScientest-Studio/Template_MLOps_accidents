import pandas as pd
from sklearn import ensemble
import joblib
import numpy as np
import os
import shutil
from check_structure import mv_existing_file_archive
import xgboost

DOCKERIZED = True
# DOCKERIZED = False

if DOCKERIZED:
    model_base = "/models"
    data_base = "/data"
    mlruns_base = "/data/mlflow/mlruns"

else:
    model_base = (
        "/home/ubuntu/Documents/Developoment/may24_bmlops_accidents/Volumes/models"
    )
    data_base = (
        "/home/ubuntu/Documents/Developoment/may24_bmlops_accidents/Volumes/data"
    )
    mlruns_base = "/home/ubuntu/Documents/Developoment/may24_bmlops_accidents/Volumes/data/mlflow/mlruns"


def push_to_production():
    mv_existing_file_archive(model_base)
    source = model_base + "/new/trained_model.joblib"
    destination = model_base + "/trained_model.joblib"
    shutil.move(source, destination)
    print("Model pushed successfully.")
    # reload model in UI
    print("Model reloaded successfully in UI.")


def Train_Model():
    print(joblib.__version__, os.getcwd())
    # execute from may24_BMLOPS_ACCIDENTS/src/models folder!
    # X_train = pd.read_csv("../../Volumes/data/preprocessed/X_train.csv")
    # X_test = pd.read_csv("../../Volumes/data/preprocessed/X_test.csv")
    # y_train = pd.read_csv("../../Volumes/data/preprocessed/y_train.csv")
    # y_test = pd.read_csv("../../Volumes/data/preprocessed/y_test.csv")
    # execute from may24_BMLOPS_ACCIDENTS folder!
    X_train = pd.read_csv(data_base + "/preprocessed/X_train.csv")
    X_test = pd.read_csv(data_base + "/preprocessed/X_test.csv")
    y_train = pd.read_csv(data_base + "/preprocessed/y_train.csv")
    y_test = pd.read_csv(data_base + "/preprocessed/y_test.csv")
    y_train = np.ravel(y_train)
    y_test = np.ravel(y_test)

    # rf_classifier = ensemble.RandomForestClassifier(n_jobs=-1)
    rf_classifier = xgboost.XGBClassifier()

    # --Train the model
    rf_classifier.fit(X_train, y_train)

    # --Save the trained model to a file
    # execute from may24_BMLOPS_ACCIDENTS folder!

    model_filename = model_base + "/new/trained_model.joblib"
    # execute from may24_BMLOPS_ACCIDENTS/src/models folder!
    # model_filename = "../../Volumes/models/trained_model.joblib"

    joblib.dump(rf_classifier, model_filename)
    print("Model trained and saved successfully.")

    loaded_model = joblib.load(model_filename)

    print("Model loaded successfully.")


if __name__ == "__main__":
    Train_Model()
