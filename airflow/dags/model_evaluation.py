from sklearn import ensemble
import sklearn.metrics as metrics
from sklearn.model_selection import train_test_split
from sklearn.dummy import DummyClassifier
import mlflow
from mlflow.models import infer_signature
from mlflow.models import MetricThreshold

# from mlflow.exceptions import ModelValidationFailedException
import shap
import pandas as pd
import xgboost
import joblib
import numpy as np
import os

DOCKERIZED = True
# DOCKERIZED = False


def evaluate_model():
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

    if DOCKERIZED:
        remote_server_uri = "http://host.docker.internal:5000"  # set to your server URI
    else:
        remote_server_uri = "http://localhost:5000"  # set to your server URI
    mlflow.set_tracking_uri(remote_server_uri)
    exp = mlflow.get_experiment_by_name(name="accidents")
    if not exp:
        experiment_id = mlflow.create_experiment(
            name="accidents"
            # artifact_location=f"file://{mlruns_base}",
        )
    else:
        experiment_id = exp.experiment_id

    print("exp.id===============================", experiment_id)

    # LOAD DATA
    X_train = pd.read_csv(data_base + "/preprocessed/X_train.csv")
    X_test = pd.read_csv(data_base + "/preprocessed/X_test.csv")
    y_train = pd.read_csv(data_base + "/preprocessed/y_train.csv")
    y_test = pd.read_csv(data_base + "/preprocessed/y_test.csv")
    y_train = np.ravel(y_train)
    y_test = np.ravel(y_test)

    # candidate_model = ensemble.RandomForestClassifier(n_jobs=-1).fit(X_train, y_train)

    model_filename = model_base + "/new/trained_model.joblib"
    model = joblib.load(model_filename)
    candidate_model = model

    # candidate_model = xgboost.XGBClassifier().fit(X_train, y_train)
    # train a baseline dummy model
    baseline_model = DummyClassifier(strategy="uniform").fit(X_train, y_train)

    # create signature that is shared by the two models
    signature = infer_signature(X_test, y_test)

    # construct an evaluation dataset from the test set
    eval_data = X_test
    eval_data["label"] = y_test

    # Define criteria for model to be validated against
    thresholds = {
        "accuracy_score": MetricThreshold(
            threshold=0.7,  # accuracy should be >=0.8
            min_absolute_change=0.05,  # accuracy should be at least 0.05 greater than baseline model accuracy
            min_relative_change=0.05,  # accuracy should be at least 5 percent greater than baseline model accuracy
            greater_is_better=True,
        ),
    }
    with mlflow.start_run(experiment_id=experiment_id) as run:
        candidate_model_uri = mlflow.sklearn.log_model(
            candidate_model, "candidate_model", signature=signature
        ).model_uri
        baseline_model_uri = mlflow.sklearn.log_model(
            baseline_model, "baseline_model", signature=signature
        ).model_uri
        try:
            exp = mlflow.get_experiment_by_name(name="accidents")
            print("In try: exp.###################################", exp)
            result = mlflow.evaluate(
                candidate_model_uri,
                eval_data,
                targets="label",
                model_type="classifier",
                # evaluators="accuracy",
                validation_thresholds=thresholds,
                baseline_model=baseline_model_uri,
            )
            print("Model validation successful")
            print(f"See aggregated evaluation results below: \n{result.metrics}")
            return True
        except:
            print("Model validation failed")
            # print(f"See aggregated evaluation results below: \n{result.metrics}")
            return False

        # result = mlflow.evaluate(
        #     candidate_model_uri,
        #     eval_data,
        #     targets="label",
        #     model_type="classifier",
        #     # evaluators="accuracy",
        #     validation_thresholds=thresholds,
        #     baseline_model=baseline_model_uri,
        # )

    return result


# evaluate_model()
