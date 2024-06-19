"""The DB tables described as classes using SQLModel."""
from typing import Optional

from sqlmodel import Field, SQLModel, BigInteger, String
from sqlalchemy import Table, Column, Integer, String, ForeignKey, MetaData

class Caracteristiques(SQLModel, table=True):
    Num_Acc: int = Field(default=None, sa_column=Column(BigInteger(), primary_key=True, autoincrement=False))
    year: int
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
    Num_Acc: int = Field(default=None, sa_column=Column(BigInteger(), foreign_key="Caracteristiques.Num_Acc"))
    year: int 
    catr: int
    voie: Optional[str] = Field(default=None, sa_column=Column(String()))
    v1: int
    v2: Optional[str] = None
    circ: int
    nbv: int
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
    Num_Acc: int = Field(default=None, sa_column=Column(BigInteger(), foreign_key="Caracteristiques.Num_Acc"))
    year: int 
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
    Num_Acc: int = Field(default=None, sa_column=Column(BigInteger(), foreign_key="Caracteristiques.Num_Acc"))
    year: int 
    id_vehicule: str = Field(default=None, sa_column=Column(String(), foreign_key="Vehicules.id_vehicule"))
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

class UsersAuth(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    password: str
