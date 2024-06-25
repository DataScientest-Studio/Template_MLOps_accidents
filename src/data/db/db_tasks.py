"""Initializing and populating the DB."""
import os
import time

from src.data.db.models import *
from src.data.db.models import Caracteristiques, Lieux, Vehicules, Users
from src.data.db.file_tasks import main as f_main
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.exc import DataError, OperationalError
from sqlalchemy import Engine
from psycopg2.errors import InvalidTextRepresentation
import tqdm
import pandas as pd
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.
host=os.getenv("POSTGRES_HOST")
database=os.getenv("POSTGRES_DB")
user=os.getenv("POSTGRES_USER")
password=os.getenv("POSTGRES_PASSWORD")
port=os.getenv("POSTGRES_PORT")
db_url = 'postgresql+psycopg2://{user}:{password}@{hostname}:{port}/{database_name}'.format(hostname=host, user=user, password=password, database_name=database, port=5432)

def create_db_engine(db_url: str) -> Engine:
    return create_engine(db_url)

def init_db(engine: Engine, sleep_for: float = 30) -> None:
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


def _add_data_to_table(engine: Engine, df: pd.DataFrame, table_model: SQLModel, year: int):
    print(f"Adding data to the '{table_model.__tablename__}' table.")

    with Session(engine) as session:
        for _, row in tqdm.tqdm(df.iterrows(), total=len(df)):
            carac = table_model(**{**row,**{"year": year}})
            session.add(carac)
        session.commit()
    print("Success!")


def add_data_to_db(engine:Engine) -> None:
    df_caract, df_places, df_users, df_veh, year = f_main()
    _add_data_to_table(engine, df=df_caract, table_model=Caracteristiques, year=year)
    _add_data_to_table(engine,df=df_places, table_model=Lieux, year=year)
    _add_data_to_table(engine,df=df_veh, table_model=Vehicules, year=year)
    _add_data_to_table(engine,df=df_users, table_model=Users, year=year)

def main():
    engine = create_db_engine(db_url=db_url)
    init_db(engine=engine)
    add_data_to_db(engine=engine)
    print("Done populating the DB, taking a long siesta...")
    while True:
        time.sleep(120)


if __name__ == "__main__":
    main()
    