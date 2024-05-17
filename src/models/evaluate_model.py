import pandas as pd 
import numpy as np
from joblib import load
import json
from pathlib import Path

from sklearn.metrics import accuracy_score

X_train = pd.read_csv('data/preprocessed/X_train.csv')
X_test = pd.read_csv('data/preprocessed/X_test.csv')
y_train = pd.read_csv('data/preprocessed/y_train.csv')
y_test = pd.read_csv('data/preprocessed/y_test.csv')
y_train = np.ravel(y_train)
y_test = np.ravel(y_test)

def main(repo_path):
    model = load(repo_path / "models/trained_model.joblib")
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    metrics = {"accuracy": accuracy}
    accuracy_path = repo_path / "metrics/accuracy.json"
    accuracy_path.write_text(json.dumps(metrics))

if __name__ == "__main__":
    repo_path = Path(__file__).parent.parent.parent
    main(repo_path)