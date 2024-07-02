from pathlib import Path

import pandas as pd
from sklearn import ensemble
import joblib
import numpy as np

print(joblib.__version__)

#execute from may24_BMLOPS_ACCIDENTS folder!
data_path = Path.cwd() / "data" / "preprocessed"

X_train = pd.read_csv(data_path / 'X_train.csv')
X_test = pd.read_csv(data_path / 'X_test.csv')
y_train = pd.read_csv(data_path / 'y_train.csv')
y_test = pd.read_csv(data_path / 'y_test.csv')

y_train = np.ravel(y_train)
y_test = np.ravel(y_test)

rf_classifier = ensemble.RandomForestClassifier(n_jobs=-1)

    # --Train the model
rf_classifier.fit(X_train, y_train)

#--Save the trained model to a file in shared Docker Volumes for the model
model_filename = '../../Volumes/model/trained_model.joblib'
joblib.dump(rf_classifier, model_filename)
print("Model trained and saved successfully.")

loaded_model = joblib.load(model_filename)

print("Model loaded successfully.")

# if __name__ == '__main__':
#     Train_Model()