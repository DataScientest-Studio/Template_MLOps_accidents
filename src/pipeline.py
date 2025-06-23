import pandas as pd
import os
import joblib
from sklearn.ensemble import RandomForestClassifier

def load_data(data_dir):
    X_train = pd.read_csv(os.path.join(data_dir, "X_train.csv"))
    y_train = pd.read_csv(os.path.join(data_dir, "y_train.csv"))
    X_test = pd.read_csv(os.path.join(data_dir, "X_test.csv"))
    y_test = pd.read_csv(os.path.join(data_dir, "y_test.csv"))
    return X_train, y_train, X_test, y_test

def train_model(X_train, y_train):
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train.values.ravel()) 
    return model

def save_model(model, model_dir="src/models"):
    import os
    os.makedirs(model_dir, exist_ok=True)
    joblib.dump(model, os.path.join(model_dir, "trained_model.joblib"))
    print("Modèle sauvegardé.")

def run_pipeline():
    # Chemin vers le dossier data/preprocessed
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'preprocessed')

    X_train, y_train, X_test, y_test = load_data(data_dir)
    model = train_model(X_train, y_train)
    save_model(model)

    print("Pipeline terminée.")

if __name__ == "__main__":
    run_pipeline()

