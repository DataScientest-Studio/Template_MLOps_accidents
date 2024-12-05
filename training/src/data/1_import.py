import os

import lakefs
import pandas as pd
from confluent_kafka import Consumer
from kafka import KafkaProducer
from lakefs.client import Client
from lakefs.exceptions import TransactionException

ISS = os.environ.get('ISS', 'http://127.0.0.1:8000')
LAKE_FS_HOST = os.environ.get('LAKE_FS_HOST', 'http://localhost:8083')
LAKE_FS_USERNAME = os.environ.get('LAKE_FS_USERNAME', 'AKIAIOSFOLQUICKSTART')
LAKE_FS_PASSWORD = os.environ.get('LAKE_FS_PASSWORD', 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY')

KAFKA_HOST = os.environ.get('KAFKA_HOST', 'localhost:9092')
KAFKA_GROUP_ID = os.environ.get('KAFKA_GROUP_ID', 'making_dataset_step')
KAFKA_OFFSET = os.environ.get('KAFKA_OFFSET', 'earliest')

INPUT_TOPIC_NAME = os.environ.get("INPUT_TOPIC_NAME", 'init_step')
OUTPUT_TOPIC_NAME = os.environ.get("OUTPUT_TOPIC_NAME", 'making_dataset_step')

clt = Client(
    host=LAKE_FS_HOST,
    username=LAKE_FS_USERNAME,
    password=LAKE_FS_PASSWORD
)

BUCKET_FOLDER_URL = 'https://mlops-project-db.s3.eu-west-1.amazonaws.com/accidents/'

kafka_producer = KafkaProducer(
    bootstrap_servers=KAFKA_HOST,
    client_id="easy_production",
    value_serializer=lambda v: v.encode('utf-8')
)

conf = {
    'bootstrap.servers': KAFKA_HOST,
    'group.id': KAFKA_GROUP_ID,
    'auto.offset.reset': KAFKA_OFFSET
}

consumer = Consumer(conf)


def download_and_sampler_file(filename, tx):
    df = pd.read_csv(os.path.join(BUCKET_FOLDER_URL, filename), sep=';')
    df = pd.concat([df, df.sample(frac=0.1)], ignore_index=True)
    tx.object('raw/' + filename).upload(df.to_csv(sep=';', index=False))


def import_data(experiment):
    branch1 = lakefs.repository('accidents', client=clt).branch(experiment).create(source_reference='main')

    try:
        with branch1.transact(commit_message='Update raw data') as tx:
            download_and_sampler_file('caracteristiques-2021.csv', tx)
            download_and_sampler_file('lieux-2021.csv', tx)
            download_and_sampler_file('vehicules-2021.csv', tx)
            download_and_sampler_file('usagers-2021.csv', tx)
    except TransactionException as inst:
        # continue if commit no changes
        if 'commit: no changes' not in inst.args[0]:
            raise inst

    kafka_producer.send(topic=OUTPUT_TOPIC_NAME, value=experiment)
    kafka_producer.flush()


def main():
    consumer.subscribe([INPUT_TOPIC_NAME])

    while True:
        msg = consumer.poll(1.0)

        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                # End of partition event
                continue
            else:
                print(msg.error())
                break
        import_data(msg.value().decode('utf-8'))


if __name__ == '__main__':
    main()
