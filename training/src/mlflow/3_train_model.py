import os

import mlflow
import numpy as np
import pandas as pd
from confluent_kafka import Consumer, KafkaError
from mlflow import MlflowClient
from sklearn import ensemble
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

os.environ['LAKECTL_SERVER_ENDPOINT_URL'] = os.environ.get('LAKE_FS_HOST', 'http://localhost:8083')
os.environ['LAKECTL_CREDENTIALS_ACCESS_KEY_ID'] = os.environ.get('LAKE_FS_USERNAME', 'AKIAIOSFOLQUICKSTART')
os.environ['LAKECTL_CREDENTIALS_SECRET_ACCESS_KEY'] = os.environ.get('LAKE_FS_PASSWORD', 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY')

KAFKA_HOST = os.environ.get('KAFKA_HOST', 'localhost:9092')
KAFKA_GROUP_ID = os.environ.get('KAFKA_GROUP_ID', 'training')
KAFKA_OFFSET = os.environ.get('KAFKA_OFFSET', 'earliest')

conf = {
    'bootstrap.servers': KAFKA_HOST,
    'group.id': KAFKA_GROUP_ID,
    'auto.offset.reset': KAFKA_OFFSET
}

c = Consumer(conf)


def train_model(experiment):
    X_train = pd.read_csv(f'lakefs://accidents/{experiment}/processed/X_train.csv', sep=';')
    X_test = pd.read_csv(f'lakefs://accidents/{experiment}/processed/X_test.csv', sep=';')
    y_train = pd.read_csv(f'lakefs://accidents/{experiment}/processed/y_train.csv', sep=';')
    y_test = pd.read_csv(f'lakefs://accidents/{experiment}/processed/y_test.csv', sep=';')

    y_train = np.ravel(y_train)
    y_test = np.ravel(y_test)

    rf_classifier = ensemble.RandomForestClassifier(n_jobs=4)

    # --Train the model
    rf_classifier.fit(X_train, y_train)

    # Evaluate model
    y_pred = rf_classifier.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)
    metrics = {'mae': mae, 'mse': mse, 'rmse': rmse, 'r2': r2}

    # Store information in tracking server
    mlflow.set_experiment('accidents')
    with mlflow.start_run(run_name=experiment) as run:
        artifact_path = 'rf_accidents'
        mlflow.log_metrics(metrics)
        mlflow.sklearn.log_model(
            sk_model=rf_classifier,
            input_example=X_test,
            artifact_path=artifact_path,
            registered_model_name='accidents_sk-learn-random-forest-class-model'
        )
        client = MlflowClient()
        model_info = client.get_latest_versions('accidents_sk-learn-random-forest-class-model')[0]
        client.set_registered_model_alias(
            name='accidents_sk-learn-random-forest-class-model',
            alias=experiment,
            version=model_info.version
        )


def main():
    c.subscribe(['training_step'])

    while True:
        msg = c.poll(1.0)

        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                # End of partition event
                continue
            else:
                print(msg.error())
                break
        train_model(msg.value().decode('utf-8'))


if __name__ == '__main__':
    main()
