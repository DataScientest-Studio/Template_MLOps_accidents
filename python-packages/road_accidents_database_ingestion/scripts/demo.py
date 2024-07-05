"""Run this script outside of docker-compose."""
from pathlib import Path
import time
import os
import dotenv

from dotenv import load_dotenv

from road_accidents_database_ingestion.db_tasks import (
    create_db_engine,
    init_db,
    get_road_accident_file2model,
    update_raw_accidents_csv_files_table,
    add_data_to_db,
    Session,
)

PATH_ROOT_PROJECT_DIR = Path.cwd().parent.parent

load_dotenv(PATH_ROOT_PROJECT_DIR)

PATH_RAW_FILES_DIR = PATH_ROOT_PROJECT_DIR / "Volumes" / "data" / "raw" / "2020"


def get_db_url() -> str:
    host = "127.0.0.1"
    database = os.getenv("ROAD_ACCIDENTS_POSTGRES_DB")
    user = os.getenv("ADMIN_USERNAME")
    password = os.getenv("ADMIN_PASSWORD")
    port = 5433
    db_url = "postgresql+psycopg2://{user}:{password}@{hostname}:{port}/{database_name}".format(
        hostname=host, user=user, password=password, database_name=database, port=port
    )
    return db_url


def main():
    db_url = get_db_url()
    engine = create_db_engine(db_url=db_url)
    init_db(engine=engine)

    file2model = get_road_accident_file2model(Path(PATH_RAW_FILES_DIR))
    with Session(engine) as session:
        update_raw_accidents_csv_files_table(db_session=session, files=file2model)
        add_data_to_db(db_session=session, files=file2model)
        session.commit()

    print("Done populating the DB, taking a long siesta...")
    while True:
        time.sleep(120)


if __name__ == "__main__":
    main()
