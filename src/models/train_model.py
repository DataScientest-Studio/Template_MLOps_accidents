import sklearn
import pandas as pd 
from sklearn import ensemble
import joblib
import numpy as np
import bentoml
from bentoml.io import NumpyNdarray

#print(joblib.__version__)

X_train = pd.read_csv('data/preprocessed/X_train.csv')
X_test = pd.read_csv('data/preprocessed/X_test.csv')
y_train = pd.read_csv('data/preprocessed/y_train.csv')
y_test = pd.read_csv('data/preprocessed/y_test.csv')
y_train = np.ravel(y_train)
y_test = np.ravel(y_test)

rf_classifier = ensemble.RandomForestClassifier(n_jobs = -1)

#--Train the model
rf_classifier.fit(X_train, y_train)

#--Test the model
rf_classifier.predict(X_test)

#--Get the model accuracy
accuracy = rf_classifier.score(X_test, y_test)

print(f"Model accuracy: {accuracy}")

# test the model on a single observation
test_data = X_test.iloc[0]
# print the actual label
print(f"Actual label: {y_test[0]}")
# print the predicted label
print(f"Predicted label: {rf_classifier.predict([test_data])[0]}")


# #--Save the trained model to a file
# model_filename = './src/models/trained_model.joblib'
# joblib.dump(rf_classifier, model_filename)
# print("Model trained and saved successfully.")
