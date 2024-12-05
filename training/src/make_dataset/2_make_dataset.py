import os

import lakefs
import numpy as np
import pandas as pd
from confluent_kafka import Consumer, KafkaError
from kafka import KafkaProducer
from lakefs.client import Client
from lakefs.exceptions import TransactionException
from lakefs_sdk import PullRequestCreation
from pydantic import StrictStr
from sklearn.model_selection import train_test_split


os.environ["LAKECTL_SERVER_ENDPOINT_URL"] = os.environ.get('LAKE_FS_HOST', 'http://localhost:8083')
os.environ["LAKECTL_CREDENTIALS_ACCESS_KEY_ID"] = os.environ.get('LAKE_FS_USERNAME', 'AKIAIOSFOLQUICKSTART')
os.environ["LAKECTL_CREDENTIALS_SECRET_ACCESS_KEY"] = os.environ.get('LAKE_FS_PASSWORD', 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY')

LAKE_FS_HOST = os.environ.get('LAKECTL_SERVER_ENDPOINT_URL')
LAKE_FS_USERNAME = os.environ.get('LAKECTL_CREDENTIALS_ACCESS_KEY_ID')
LAKE_FS_PASSWORD = os.environ.get('LAKECTL_CREDENTIALS_SECRET_ACCESS_KEY')

KAFKA_HOST = os.environ.get('KAFKA_HOST', 'localhost:9092')
KAFKA_GROUP_ID = os.environ.get('KAFKA_GROUP_ID', 'make_dataset')
KAFKA_OFFSET = os.environ.get('KAFKA_OFFSET', 'earliest')

INPUT_TOPIC_NAME = os.environ.get("INPUT_TOPIC_NAME", 'making_dataset_step')
OUTPUT_TOPIC_NAME = os.environ.get("OUTPUT_TOPIC_NAME", 'training_step')

clt = Client(
    host=LAKE_FS_HOST,
    username=LAKE_FS_USERNAME,
    password=LAKE_FS_PASSWORD
)

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


def process_data(experiment):
    # --Importing dataset
    df_users = pd.read_csv(f"lakefs://accidents/{experiment}/raw/usagers-2021.csv", sep=";")
    df_caract = pd.read_csv(f"lakefs://accidents/{experiment}/raw/caracteristiques-2021.csv", sep=";", header=0,
                            low_memory=False)
    df_places = pd.read_csv(f"lakefs://accidents/{experiment}/raw/lieux-2021.csv", sep=";", encoding='utf-8')
    df_veh = pd.read_csv(f"lakefs://accidents/{experiment}/raw/vehicules-2021.csv", sep=";")

    # --Creating new columns
    nb_victim = pd.crosstab(df_users.Num_Acc, "count").reset_index()
    nb_vehicules = pd.crosstab(df_veh.Num_Acc, "count").reset_index()
    df_users["year_acc"] = df_users["Num_Acc"].astype(str).apply(lambda x: x[:4]).astype(int)
    df_users["victim_age"] = df_users["year_acc"] - df_users["an_nais"]
    for i in df_users["victim_age"]:
        if (i > 120) | (i < 0):
            df_users["victim_age"].replace(i, np.nan)
    df_caract["hour"] = df_caract["hrmn"].astype(str).apply(lambda x: x[:-3])
    df_caract.drop(['hrmn', 'an'], inplace=True, axis=1)
    df_users.drop(['an_nais'], inplace=True, axis=1)

    # --Replacing names
    df_users.grav.replace([1, 2, 3, 4], [1, 3, 4, 2], inplace=True)
    df_caract.rename({"agg": "agg_"}, inplace=True, axis=1)
    corse_replace = {"2A": "201", "2B": "202"}
    df_caract["dep"] = df_caract["dep"].str.replace("2A", "201")
    df_caract["dep"] = df_caract["dep"].str.replace("2B", "202")
    df_caract["com"] = df_caract["com"].str.replace("2A", "201")
    df_caract["com"] = df_caract["com"].str.replace("2B", "202")

    # --Converting columns types
    df_caract[["dep", "com", "hour"]] = df_caract[["dep", "com", "hour"]].astype(int)

    dico_to_float = {'lat': float, 'long': float}
    df_caract["lat"] = df_caract["lat"].str.replace(',', '.')
    df_caract["long"] = df_caract["long"].str.replace(',', '.')
    df_caract = df_caract.astype(dico_to_float)

    # --Grouping modalities
    dico = {1: 0, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 0, 9: 0}
    df_caract["atm"] = df_caract["atm"].replace(dico)
    catv_value = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 30, 31, 32, 33, 34, 35,
                  36, 37, 38, 39, 40, 41, 42, 43, 50, 60, 80, 99]
    catv_value_new = [0, 1, 1, 2, 1, 1, 6, 2, 5, 5, 5, 5, 5, 4, 4, 4, 4, 4, 3, 3, 4, 4, 1, 1, 1, 1, 1, 6, 6, 3, 3, 3, 3,
                      1, 1, 1, 1, 1, 0, 0]
    df_veh['catv'].replace(catv_value, catv_value_new, inplace=True)

    # --Merging datasets
    fusion1 = df_users.merge(df_veh, on=["Num_Acc", "num_veh", "id_vehicule"], how="inner")
    fusion1 = fusion1.sort_values(by="grav", ascending=False)
    fusion1 = fusion1.drop_duplicates(subset=['Num_Acc'], keep="first")
    fusion2 = fusion1.merge(df_places, on="Num_Acc", how="left")
    df = fusion2.merge(df_caract, on='Num_Acc', how="left")

    # --Adding new columns
    df = df.merge(nb_victim, on="Num_Acc", how="inner")
    df.rename({"count": "nb_victim"}, axis=1, inplace=True)
    df = df.merge(nb_vehicules, on="Num_Acc", how="inner")
    df.rename({"count": "nb_vehicules"}, axis=1, inplace=True)

    # --Modification of the target variable  : 1 : prioritary // 0 : non-prioritary
    df['grav'].replace([2, 3, 4], [0, 1, 1], inplace=True)

    # --Replacing values -1 and 0
    col_to_replace0_na = ["trajet", "catv", "motor"]
    col_to_replace1_na = ["trajet", "secu1", "catv", "obsm", "motor", "circ", "surf", "situ", "vma", "atm", "col"]
    df[col_to_replace1_na] = df[col_to_replace1_na].replace(-1, np.nan)
    df[col_to_replace0_na] = df[col_to_replace0_na].replace(0, np.nan)

    # --Dropping columns
    list_to_drop = ['senc', 'larrout', 'actp', 'manv', 'choc', 'nbv', 'prof', 'plan', 'Num_Acc', 'id_vehicule',
                    'num_veh', 'pr', 'pr1', 'voie', 'trajet', "secu2", "secu3", 'adr', 'v1', 'lartpc', 'occutc', 'v2',
                    'vosp', 'locp', 'etatp', 'infra', 'obs']
    df.drop(list_to_drop, axis=1, inplace=True)

    # --Dropping lines with NaN values
    col_to_drop_lines = ['catv', 'vma', 'secu1', 'obsm', 'atm']
    df = df.dropna(subset=col_to_drop_lines, axis=0)

    target = df['grav']
    feats = df.drop(['grav'], axis=1)

    X_train, X_test, y_train, y_test = train_test_split(feats, target, test_size=0.3, random_state=42)

    # --Filling NaN values
    col_to_fill_na = ["surf", "circ", "col", "motor"]
    X_train[col_to_fill_na] = X_train[col_to_fill_na].fillna(X_train[col_to_fill_na].mode().iloc[0])
    X_test[col_to_fill_na] = X_test[col_to_fill_na].fillna(X_train[col_to_fill_na].mode().iloc[0])

    branch = lakefs.repository("accidents", client=clt).branch(experiment)

    try:
        with branch.transact(commit_message="Update processed data") as tx:
            for file, filename in zip([X_train, X_test, y_train, y_test], ['X_train', 'X_test', 'y_train', 'y_test']):
                tx.object(f'processed/{filename}.csv').upload(file.to_csv(sep=";", index=False))
    except TransactionException as inst:
        # continue if commit no changes
        if 'commit: no changes' not in inst.args[0]:
            raise inst

    pull_request_creation = PullRequestCreation(
        title="Feat: " + experiment,
        description=experiment,
        source_branch=experiment,
        destination_branch=StrictStr('main')
    )
    clt.sdk_client.pulls_api.create_pull_request('accidents', pull_request_creation)

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
        process_data(msg.value().decode('utf-8'))


if __name__ == '__main__':
    main()
