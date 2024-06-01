import sys
import sklearn
import pandas as pd 
#from sklearn import ensemble
import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression


if __name__ == "__main__":
    s_tol = float(sys.argv[1])          # 0.001
    s_max_iter = int(sys.argv[2])       # 100
    
    print(joblib.__version__)
    
    
    X_train = pd.read_csv('data/processed/X_train.csv')
    X_test = pd.read_csv('data/processed/X_test.csv')
    y_train = pd.read_csv('data/processed/y_train.csv')
    y_test = pd.read_csv('data/processed/y_test.csv')
    
    
    y_train = np.ravel(y_train)
    y_test = np.ravel(y_test)
    
    #rf_classifier = ensemble.RandomForestClassifier(n_jobs = -1)
    log_reg = LogisticRegression(tol=s_tol, solver='liblinear', max_iter=s_max_iter, verbose=1, random_state=3)
    
    #--Train the model
    #rf_classifier.fit(X_train, y_train)
    log_reg.fit(X_train, y_train)
    
    #--Save the trained model to a file
    model_filename = './src/models/log_reg_trained_model.joblib'
    #joblib.dump(rf_classifier, model_filename)
    joblib.dump(log_reg, model_filename)
    
    print("Model trained and saved successfully.")
