from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import pytest
from src.data.db.db_tasks import init_db, add_data_to_db
from unittest import mock

from tests.data.db.constants import DF_CARAC, DF_PLACES, DF_USERS, DF_VEH
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_init_db():
    init_db(engine)
    df_caract, df_places, df_users, df_veh = DF_CARAC, DF_PLACES, DF_USERS, DF_VEH
    with mock.patch('src.data.db.db_tasks.f_main', mock.MagicMock(return_value=[df_caract, df_places, df_users, df_veh, 2021])):
        add_data_to_db(engine)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert tables