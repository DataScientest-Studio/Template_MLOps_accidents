import sklearn.metrics as metrics
import pickle
import joblib
import json
import numpy as np
import pandas as pd
from datetime import datetime

model_base = '/Users/drjosefhartmann/Development/Accidents/may24_bmlops_accidents/airflow/Volumes/models'
data_base = '/Users/drjosefhartmann/Development/Accidents/may24_bmlops_accidents/airflow/Volumes/data'
metrics_base = '/Users/drjosefhartmann/Development/Accidents/may24_bmlops_accidents/airflow/Volumes/metrics'
predictions_base = '/Users/drjosefhartmann/Development/Accidents/may24_bmlops_accidents/airflow/Volumes/predictions'
def evaluate():
    print("Model Evaluation")
    X_test = pd.read_csv(data_base + "/preprocessed/X_test.csv")
    y_test = pd.read_csv(data_base + "/preprocessed/y_test.csv")

    y_test = y_test.values.ravel()
    
    model_filename =  model_base + "/trained_model.joblib"
    model = joblib.load(model_filename)

    predictions = model.predict(X_test)
 
    prediction_csv = pd.DataFrame({"target_labels": y_test, "predicted_labels": predictions})
    prediction_filename = predictions_base + f'/prediction_{datetime.today().strftime("%Y%m%d%H%M%S")}.csv'
    prediction_csv.to_csv(prediction_filename, index=False)

    mse = metrics.mean_squared_error(y_test, predictions)
    r2 = metrics.r2_score(y_test, predictions)
    metrics_filename = metrics_base +  f'/scores_{datetime.today().strftime("%Y%m%d%H%M%S")}.json'
    with open(metrics_filename, "w") as fd:
        json.dump({"mse": mse, "r2": r2}, fd, indent=4)


if __name__ == '__main__':
    evaluate()
