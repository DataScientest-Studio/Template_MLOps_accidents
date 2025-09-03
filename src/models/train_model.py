import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib
import mlflow
import mlflow.sklearn
import bentoml
import os
from pathlib import Path

print(f"Joblib version: {joblib.__version__}")

# Set MLflow tracking URI to a local directory
mlflow_tracking_path = Path("./mlruns")
mlflow_tracking_path.mkdir(parents=True, exist_ok=True)
mlflow.set_tracking_uri(f"file://{mlflow_tracking_path.absolute()}")
mlflow.set_experiment("Accident_Prediction")

# Load data
X_train = pd.read_csv('data/preprocessed/X_train_clean.csv')
X_test = pd.read_csv('data/preprocessed/X_test_clean.csv')
y_train = pd.read_csv('data/preprocessed/y_train.csv')
y_test = pd.read_csv('data/preprocessed/y_test.csv')

# Flatten labels
y_train = np.ravel(y_train)
y_test = np.ravel(y_test)

# One-hot encode and align columns
X_train = pd.get_dummies(X_train)
X_test = pd.get_dummies(X_test)
X_test = X_test.reindex(columns=X_train.columns, fill_value=0)

# Convert int columns to float64 to avoid schema issues (THIS WAS BROKEN BEFORE!)
X_train = X_train.astype({col: 'float64' for col in X_train.select_dtypes(include='int').columns})
X_test = X_test.astype({col: 'float64' for col in X_test.select_dtypes(include='int').columns})

# Save the column names used for training (important for serving)
columns_filename = "src/models/trained_model_columns.npy"
np.save(columns_filename, X_train.columns.values)
print(f"✅ Model columns saved as: {columns_filename}")

# Train model
rf_classifier = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
rf_classifier.fit(X_train, y_train)

# Evaluate
y_pred = rf_classifier.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"✅ Accuracy: {accuracy:.4f}")

# Save model locally
model_filename = "src/models/trained_model.joblib"
joblib.dump(rf_classifier, model_filename)
print(f"✅ Model saved locally as: {model_filename}")

# Log parameters, metrics, and model to MLflow
with mlflow.start_run():
    mlflow.log_param("n_estimators", 100)
    mlflow.log_param("random_state", 42)
    mlflow.log_metric("accuracy", accuracy)
    try:
        mlflow.sklearn.log_model(
            sk_model=rf_classifier,
            artifact_path="model",
            input_example=X_train.iloc[:5],
            signature=mlflow.models.infer_signature(X_train, y_train)
        )
        print("✅ Model successfully logged to MLflow")
    except Exception as e:
        print(f"❌ MLflow logging failed: {e}")

    # Log artifact to MLflow
    try:
        mlflow.log_artifact(model_filename, artifact_path="model_artifacts")
        mlflow.log_artifact(columns_filename, artifact_path="model_artifacts")
        print("✅ Model artifact logged to MLflow")
    except Exception as e:
        print(f"⚠️ MLflow artifact logging failed: {e}")

# Optionally save with BentoML
try:
    bentoml.sklearn.save_model("predict_model", rf_classifier)
    print("✅ Model saved to BentoML successfully.")
except Exception as e:
    print(f"❌ BentoML saving failed: {e}")

print("\n🎉 Training completed!")
print(f"📊 Final accuracy: {accuracy:.4f}")
print("✅ Model saved and metrics logged successfully.")

