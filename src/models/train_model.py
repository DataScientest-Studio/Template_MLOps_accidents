
import sklearn
import pandas as pd 
from sklearn import ensemble
from sklearn.metrics import f1_score, make_scorer
from sklearn.model_selection import train_test_split
import joblib
from sklearn.model_selection import cross_val_score, GridSearchCV

df = pd.read_csv('data/preprocessed/preprocessed.csv')

target = df['grav']
feats = df.drop(['grav'], axis = 1)

X_train, X_test, y_train, y_test = train_test_split(feats, target, test_size=0.3, random_state = 42)


rf_classifier = ensemble.RandomForestClassifier(n_jobs = -1, n_estimators= 100)

# Perform the grid search on the data
rf_classifier.fit(X_train, y_train)

# Save the trained model to a file
model_filename = 'trained_model.joblib'
joblib.dump(rf_classifier, model_filename)
print("Model trained and saved successfully.")
