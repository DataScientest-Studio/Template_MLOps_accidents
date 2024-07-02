import pandas as pd
from sklearn import ensemble
import joblib
import numpy as np
import os
from model_api.feature_extraction.check_structure import mv_existing_file_archive


model_base = "/Users/drjosefhartmann/Development/Accidents/may24_bmlops_accidents/airflow/Volumes/models"
data_base = "/Users/drjosefhartmann/Development/Accidents/may24_bmlops_accidents/airflow/Volumes/data"


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

    rf_classifier = ensemble.RandomForestClassifier(n_jobs=-1)

    # --Train the model
    rf_classifier.fit(X_train, y_train)

    # --Save the trained model to a file
    # execute from may24_BMLOPS_ACCIDENTS folder!

    model_filename = model_base + "/trained_model.joblib"
    # execute from may24_BMLOPS_ACCIDENTS/src/models folder!
    # model_filename = "../../Volumes/models/trained_model.joblib"

    mv_existing_file_archive(model_base)

    joblib.dump(rf_classifier, model_filename)
    print("Model trained and saved successfully.")

    loaded_model = joblib.load(model_filename)

    print("Model loaded successfully.")


# if __name__ == '__main__':
#     Train_Model()
