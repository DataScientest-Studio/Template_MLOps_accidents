"""Initializing and populating the DB."""

import os
import time
from pathlib import Path
from typing import Dict

from sqlmodel import SQLModel, create_engine, Session, select
from sqlalchemy.exc import OperationalError
import tqdm
import pandas as pd
from dotenv import load_dotenv

from road_accidents_database_ingestion.models import *
from road_accidents_database_ingestion.models import (
    Caracteristiques,
    Lieux,
    Vehicules,
    Users,
)
from road_accidents_database_ingestion.file_tasks import get_dataframe

load_dotenv()  # take environment variables from .env.


def get_db_url() -> str:
    host = os.getenv("ROAD_ACCIDENTS_POSTGRES_HOST")
    database = os.getenv("ROAD_ACCIDENTS_POSTGRES_DB")
    user = os.getenv("ADMIN_USERNAME")
    password = os.getenv("ADMIN_PASSWORD")
    port = os.getenv("ROAD_ACCIDENTS_POSTGRES_PORT")
    db_url = "postgresql+psycopg2://{user}:{password}@{hostname}:{port}/{database_name}".format(
        hostname=host, user=user, password=password, database_name=database, port=port
    )
    return db_url


def create_db_engine(db_url: str):
    return create_engine(db_url)


def init_db(engine, sleep_for: float = 30) -> None:
    """Create DB tables based on the SqlModels."""
    while True:
        try:
            print("Trying to create the DB tables")
            SQLModel.metadata.create_all(engine)
        except OperationalError:
            print("Failed... Attempting again.")
            time.sleep(sleep_for)
        except Exception:
            raise
        else:
            print("Tables created.")
            break


def _add_data_to_table(db_session: Session, df: pd.DataFrame, table_model: SQLModel):
    print(f"Adding data to the '{table_model.__tablename__}' table.")

    for _, row in tqdm.tqdm(
        df.iterrows(),
        total=len(df),
        desc=f"Updating table: '{table_model.__tablename__}'",
        mininterval=1.0,
    ):
        carac = table_model(**row)
        db_session.add(carac)
    db_session.commit()


def update_raw_accidents_csv_files_table(
    db_session: Session,
    files: Dict[RawRoadAccidentCsvFileNames, RawRoadAccidentsCsvFile],
) -> None:
    for road_acc_type, road_acc_file in files.items():
        print(
            f"Checking if file `{road_acc_file.file_name}` has already been processed using its md5=`{road_acc_file.md5}`"
        )
        db_table_entries = select(RawRoadAccidentsCsvFile).where(
            RawRoadAccidentsCsvFile.md5 == road_acc_file.md5
        )
        results = list(db_session.exec(db_table_entries))
        if any([r.processing_status == ProcessingStatus.processed for r in results]):
            print(
                f"File `{road_acc_file.dir_name}/`{road_acc_file.file_name}` has already been processed. Skipping..."
            )
            road_acc_file.processing_status = ProcessingStatus.processed
            continue

        print(f"Adding file `{road_acc_file.file_name}` to the DB.")
        db_session.add(road_acc_file)
    db_session.commit()
    print("Success!")


def add_data_to_db(db_session: Session, files) -> bool:
    """_summary_

    Args:
        db_session:
        files:

    Returns:
        - `True` if new data added to the DB
        - `False` if no new data added to the DB

    Raises:
        RuntimeError:
            If something went wrong while adding rows to the DB table.
    """
    new_data_added_to_db = None
    order_files = [
        RawRoadAccidentCsvFileNames.caracteristiques,
        RawRoadAccidentCsvFileNames.lieux,
        RawRoadAccidentCsvFileNames.vehicules,
        RawRoadAccidentCsvFileNames.usagers,
    ]

    for raw_csv_type in order_files:
        if not (road_acc_model := files.get(raw_csv_type)):
            new_data_added_to_db = (
                False if new_data_added_to_db is None else new_data_added_to_db
            )
            continue

        if road_acc_model.processing_status == ProcessingStatus.processed:
            new_data_added_to_db = (
                False if new_data_added_to_db is None else new_data_added_to_db
            )
            continue

        df = get_dataframe(road_acc_model.path)
        if raw_csv_type == RawRoadAccidentCsvFileNames.caracteristiques:
            table_model = Caracteristiques
        elif raw_csv_type == RawRoadAccidentCsvFileNames.lieux:
            table_model = Lieux
        elif raw_csv_type == RawRoadAccidentCsvFileNames.usagers:
            table_model = Users
        elif raw_csv_type == RawRoadAccidentCsvFileNames.vehicules:
            table_model = Vehicules
        else:
            raise RuntimeError(f"Unknown road accidents raw file `{raw_csv_type}`!")
        try:
            _add_data_to_table(db_session, df=df, table_model=table_model)
            road_acc_model.processing_status = ProcessingStatus.processed
        except Exception as e:  # TODO use correct sqlalchemy exception
            print(
                f"Error while adding `{raw_csv_type}` data to the `{table_model}` table. Exception: `{e}`"
            )
            road_acc_model.processing_status = ProcessingStatus.failed
            road_acc_model.reason = f"Exception raised: {e}"
        finally:
            db_session.add(road_acc_model)
            new_data_added_to_db = True

    return new_data_added_to_db
