import sklearn.metrics as metrics
import pickle
import joblib
import json
import numpy as np
import pandas as pd
from datetime import datetime
import os
import subprocess


model_base = "/models"
data_base = "/data"
metrics_base = "/data/metrics"
predictions_base = "/data/predictions"


def evaluate():
    print("Model Evaluation")
    X_test = pd.read_csv(data_base + "/preprocessed/X_test.csv")
    y_test = pd.read_csv(data_base + "/preprocessed/y_test.csv")

    y_test = y_test.values.ravel()

    if not os.path.exists(metrics_base):
        subprocess.call(["sudo mkdir", "-m", "777", "metrics_base"])
    if not os.path.exists(predictions_base):
        subprocess.call(["sudo mkdir", "-m", "777", "predictions_base"])
    # subprocess.call(['chmod', '-R', '777', 'metrics_base'])
    # subprocess.call(['chmod', '-R', '777', 'prediction_base'])

    model_filename = model_base + "/new/trained_model.joblib"
    model = joblib.load(model_filename)

    predictions = model.predict(X_test)

    prediction_csv = pd.DataFrame(
        {"target_labels": y_test, "predicted_labels": predictions}
    )
    prediction_filename = (
        predictions_base
        + f'/prediction_{datetime.today().strftime("%Y%m%d%H%M%S")}.csv'
    )
    prediction_csv.to_csv(prediction_filename, index=False)

    mse = metrics.mean_squared_error(y_test, predictions)
    r2 = metrics.r2_score(y_test, predictions)
    accuracy = metrics.accuracy_score(y_test, predictions)
    f1_score = metrics.f1_score(y_test, predictions)
    metrics_filename = (
        metrics_base + f'/scores_{datetime.today().strftime("%Y%m%d%H%M%S")}.json'
    )
    with open(metrics_filename, "w") as fd:
        json.dump(
            {"acc": accuracy, "f1-score": f1_score, "mse": mse, "r2": r2}, fd, indent=4
        )


if __name__ == "__main__":
    evaluate()
