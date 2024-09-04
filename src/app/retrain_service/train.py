import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from datetime import datetime

data_path = "../../src/data/data_2005a2021.csv"
data = pd.read_csv(data_path)

X = data.drop(columns=['grav'])  
y = data['grav']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestClassifier(random_state=42)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

# Ajout versionning avec la date et heure du ré-entrainement
retrain_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

model_data = {
    'model': model,
    'accuracy': accuracy,
    'retrain_timestamp': retrain_timestamp 
}

model_path = "../../models/model_rf_clf.pkl"
with open(model_path, 'wb') as model_file:
    joblib.dump(model_data, model_file)

print(f"Modèle réentraîné avec succès avec une accuracy de {accuracy:.2f} le {retrain_timestamp}")

