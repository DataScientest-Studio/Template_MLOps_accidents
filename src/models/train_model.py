# import sklearn
import pandas as pd
from sklearn import ensemble
import joblib
import numpy as np
import os
from pathlib import Path


def train_and_save_model(model_name="trained_model"):
    # paths:
    root_path = Path(os.path.realpath(__file__)).parents[2]
    path_data_preprocessed = os.path.join(root_path, "data", "preprocessed")
    path_X_train = os.path.join(path_data_preprocessed, "X_train.csv")
    path_y_train = os.path.join(path_data_preprocessed, "y_train.csv")
    path_model = os.path.join(root_path, "models")

    # Train import:
    X_train = pd.read_csv(path_X_train)
    y_train = pd.read_csv(path_y_train)
    y_train = np.ravel(y_train)

    rf_classifier = ensemble.RandomForestClassifier(n_jobs=-1)

    # -- Train the model
    rf_classifier.fit(X_train, y_train)

    # -- Save the trained model to a file
    model_filename = os.path.join(path_model, f"{model_name}.joblib")
    joblib.dump(rf_classifier, model_filename)
    print(f"Model {model_name}.joblib trained and saved successfully.")


def train_without_saving():
    # paths:
    root_path = Path(os.path.realpath(__file__)).parents[2]
    path_data_preprocessed = os.path.join(root_path, "data", "preprocessed")
    path_X_train = os.path.join(path_data_preprocessed, "eval_X_train.csv")
    path_y_train = os.path.join(path_data_preprocessed, "eval_y_train.csv")
    path_model = os.path.join(root_path, "models")

    # Train import:
    X_train = pd.read_csv(path_X_train)
    y_train = pd.read_csv(path_y_train)
    y_train = np.ravel(y_train)

    rf_classifier = ensemble.RandomForestClassifier(n_jobs=-1)

    # -- Train the model
    rf_classifier.fit(X_train, y_train)

    return rf_classifier


if __name__ == '__main__':
    train_and_save_model()
