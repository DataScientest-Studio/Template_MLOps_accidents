"""The DB tables described as classes using SQLModel."""
from typing import Optional
from datetime import datetime

from sqlmodel import Field, SQLModel, BigInteger, String, Enum
from sqlalchemy import Table, Column, Integer, String, ForeignKey, MetaData

from road_accidents_database_ingestion.enums import ProcessingStatus, RawRoadAccidentCsvFileNames

class RawRoadAccidentsCsvFile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    raw_accident_file: RawRoadAccidentCsvFileNames = Field(sa_column=Column(Enum(RawRoadAccidentCsvFileNames)))
    file_name: str
    dir_name: str
    path: str
    md5: str
    sha256: str
    processing_status: ProcessingStatus = Field(sa_column=Column(Enum(ProcessingStatus), default=ProcessingStatus.processing))
    reason: Optional[str] = None
    created_at: datetime = Field(default=datetime.utcnow(), nullable=False)
    last_edited: datetime = Field(default_factory=datetime.utcnow, nullable=False)

class Caracteristiques(SQLModel, table=True):
    Num_Acc: int = Field(default=None, sa_column=Column(BigInteger(), primary_key=True, autoincrement=False))
    jour: int
    mois: int
    an: int
    hrmn: str
    lum: int
    dep: str
    com: str
    agg: int
    int: int
    atm: int
    col: int
    adr: Optional[str] = None
    lat: str
    long: str


class Lieux(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    Num_Acc: int = Field(default=None, sa_column=Column(BigInteger(), ForeignKey("caracteristiques.Num_Acc", onupdate="CASCADE")))
    catr: int
    voie: Optional[str] = Field(default=None, sa_column=Column(String()))
    v1: int
    v2: Optional[str] = None
    circ: int
    nbv: Optional[int] = None
    vosp: int
    prof: int
    pr: str
    pr1: str
    plan: int
    lartpc: Optional[str] = None
    larrout: str
    surf: int
    infra: int
    situ: int
    vma: int

class Vehicules(SQLModel, table=True):
    id_vehicule: str = Field(default=None, primary_key=True)
    Num_Acc: int = Field(default=None, sa_column=Column(BigInteger(), ForeignKey("caracteristiques.Num_Acc", onupdate="CASCADE")))
    num_veh: str
    senc: int
    catv: int
    obs: int
    obsm: int
    choc: int
    manv: int 
    motor: int
    occutc: Optional[float] = None


class Users(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    Num_Acc: int = Field(default=None, sa_column=Column(BigInteger(), ForeignKey("caracteristiques.Num_Acc", onupdate="CASCADE")))
    id_vehicule: str = Field(default=None, sa_column=Column(String(), ForeignKey("vehicules.id_vehicule", onupdate="CASCADE")))
    num_veh: str
    place: int
    catu: int
    grav: int
    sexe: int
    an_nais: Optional[float] = None
    trajet: int
    secu1: int
    secu2: int
    secu3: int
    locp: int
    actp: str
    etatp: str
