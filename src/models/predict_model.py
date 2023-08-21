
import click
import joblib
import pandas as pd

# Load your saved model
loaded_model = joblib.load("src/models/trained_model.joblib")

@click.command()
def main():
    # Load your training dataset (replace 'train_data.csv' with your file)
    X_train = pd.read_csv("data/preprocessed/X_train.csv")

    # Get feature names from X_train columns
    feature_names = X_train.columns.tolist()

    features = {}

    # Get user input for each feature
    for feature_name in feature_names:
        feature_value = click.prompt(f"Enter value for {feature_name}", type=float)
        features[feature_name] = feature_value

    # Predict using the model
    result = predict_model(features)
    print("Prediction:", result)

def predict_model(features):
    input_df = pd.DataFrame([features])
    prediction = loaded_model.predict(input_df)
    return prediction

if __name__ == "__main__":
    main()

