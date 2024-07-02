from pathlib import Path

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import select, Session
import pytest

from road_accidents_database_ingestion.db_tasks import (
    init_db,
    add_data_to_db,
    update_raw_accidents_csv_files_table,
)
from road_accidents_database_ingestion.models import RawRoadAccidentsCsvFile
from road_accidents_database_ingestion.enums import ProcessingStatus
from road_accidents_database_ingestion.file_tasks import get_road_accident_file2model

import tests.road_accidents_database_ingestion.constants as c


@pytest.fixture(scope="function")
def db_session():

    SQLALCHEMY_DATABASE_URL = "sqlite://"

    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    init_db(engine)
    with Session(engine) as session:
        yield session


def test_update_raw_accidents_csv_files_table(temp_dir, db_session):
    c.create_raw_road_accident_files_in_dir(temp_dir)

    file2model = get_road_accident_file2model(temp_dir)
    update_raw_accidents_csv_files_table(db_session, files=file2model)
    statement = select(RawRoadAccidentsCsvFile)
    table_rows = db_session.exec(statement).all()
    for tbr in table_rows:
        assert file2model[tbr.raw_accident_file].md5 == tbr.md5
        assert tbr.processing_status == ProcessingStatus.processing

    update_raw_accidents_csv_files_table(db_session, files=file2model)
    statement = select(RawRoadAccidentsCsvFile)
    table_rows = db_session.exec(statement).all()
    for tbr in table_rows:
        assert file2model[tbr.raw_accident_file].md5 == tbr.md5
        assert tbr.processing_status == ProcessingStatus.processing


def test_add_data_to_db(temp_dir, db_session):
    c.create_raw_road_accident_files_in_dir(temp_dir)

    file2model = get_road_accident_file2model(temp_dir)
    update_raw_accidents_csv_files_table(db_session, files=file2model)
    add_data_to_db(db_session, files=file2model)
    statement = select(RawRoadAccidentsCsvFile)
    table_rows = db_session.exec(statement).all()
    for tbr in table_rows:
        assert file2model[tbr.raw_accident_file].md5 == tbr.md5
        assert tbr.processing_status == ProcessingStatus.processed
