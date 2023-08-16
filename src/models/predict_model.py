import joblib
from imblearn.metrics import classification_report_imbalanced

# Load the trained model from the file
model_filename = 'trained_model.joblib'
loaded_model = joblib.load(model_filename)

y_pred = loaded_model.predict(X_test)



print(f1_score(y_test, y_pred_rf))
pd.crosstab(y_test, y_pred, rownames=['Classe réelle'], colnames=['Classe prédite'])
print(classification_report_imbalanced(y_test, y_pred))