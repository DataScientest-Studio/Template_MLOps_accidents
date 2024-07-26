import joblib
import pandas as pd
import sklearn.metrics as metrics
import sys
import json
from datetime import datetime
import os

# Load your saved model
loaded_model = joblib.load("./src/models/trained_model.joblib")
# Load some test_features json files
test_features0 = './src/models/features_example/test_features0.json'
test_features1 = './src/models/features_example/test_features1.json'

def predict_model(features):
    input_df = pd.DataFrame([features])
    print(input_df)
    prediction = loaded_model.predict(input_df)
    return prediction

def evaluate_model():
    X_test = pd.read_csv("./data/processed/X_test.csv")
    y_test = pd.read_csv("./data/processed/y_test.csv")

    y_test = y_test.values.ravel()

    predictions = loaded_model.predict(X_test)
 
    prediction_csv = pd.DataFrame({"target": y_test, "predicted": predictions})
    if not os.path.isdir("src/models/predictions"):
        os.makedirs("src/models/predictions")
    #prediction_filename = f'src/models/predictions/prediction_{datetime.today().strftime("%Y%m%d%H%M%S")}.csv'
    prediction_filename = f'src/models/predictions/predictions.csv'
    prediction_csv.to_csv(prediction_filename, index=False, header=True)

    mse = metrics.mean_squared_error(y_test, predictions)
    recall = metrics.recall_score(y_test, predictions)
    precision = metrics.precision_score(y_test, predictions)
    f1 = metrics.f1_score(y_test, predictions)

    if not os.path.isdir("src/models/scores"):
        os.makedirs("src/models/scores")
    #metrics_filename = f'src/models/scores/scores_{datetime.today().strftime("%Y%m%d%H%M%S")}.json'
    metrics_filename = f'src/models/scores/scores.json'
    with open(metrics_filename, "w") as fd:
        json.dump({"mse": mse, "precision": precision, "recall": recall, "f1": f1}, fd, indent=2)

    #print(prediction_filename)

    input_df = pd.json_normalize(json.load(open(test_features0)))
    prediction = loaded_model.predict(input_df)
    return int(prediction[0])   # convert np.int64 to int to avoid json exception

if __name__ == "__main__":
    if len(sys.argv) == 2:
        json_file = sys.argv[1]
        with open(json_file, 'r') as file:
            features = json.load(file)
    else:
        #we can predict using json file test_features0 (which predicts 0) or test_features1 (which predicts 1)
        test_features = test_features0
        #test_features = test_features1
        features = json.load(open(test_features))

    result = predict_model(features)
    print(f"prediction : {result[0]}")

    evaluate_model()