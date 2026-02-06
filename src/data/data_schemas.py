"""
Data Schemas for validating road accident data using Pandera.

This module defines schemas for users, characteristics, vehicles, and places data that can be found under `./data/raw/`,
where the data types and value ranges are specified in `./references/description-des-bases-de-donnees-annuelles.pdf`.
"""

import pandera.pandas as pa


class UserSchema(pa.DataFrameModel):
    Num_Acc: int = pa.Field(ge=200000000001, le=202699999999)
    id_vehicule: str = pa.Field(str_matches=r"^\d{3}.{1,2}\d{3}$")
    num_veh: str = pa.Field(str_matches=r"^[A-Z\[\]]{1,2}\d{2}$")
    place: int = pa.Field(ge=-1, le=10, ne=0, nullable=True)
    catu: int = pa.Field(ge=1, le=3, nullable=True)
    grav: int = pa.Field(ge=-1, le=4, ne=0, nullable=True)
    sexe: int = pa.Field(ge=-1, le=2, ne=0, nullable=True)
    an_nais: float = pa.Field(ge=1900, le=2026, nullable=True)
    trajet: int = pa.Field(ge=-1, le=9, nullable=True)
    secu1: int = pa.Field(ge=-1, le=9, nullable=True)
    secu2: int = pa.Field(ge=-1, le=9, nullable=True)
    secu3: int = pa.Field(ge=-1, le=9, nullable=True)
    locp: int = pa.Field(ge=-1, le=9, nullable=True)
    actp: str = pa.Field(str_matches=r"^\s*(?:-1|\d|A|B)$", nullable=True)
    etatp: int = pa.Field(ge=-1, le=3, ne=0, nullable=True)

    class Config:
        name = "UserSchema"
        coerce = True


class CharactSchema(pa.DataFrameModel):
    Num_Acc: int = pa.Field(ge=200000000001, le=202699999999, unique=True)
    jour: int = pa.Field(ge=1, le=31, nullable=True)
    mois: int = pa.Field(ge=1, le=12, nullable=True)
    an: int = pa.Field(ge=2000, le=2026, nullable=True)
    hrmn: str = pa.Field(str_matches=r"^(?:[01]\d|2[0-3]):[0-5]\d$", nullable=True)
    lum: int = pa.Field(ge=1, le=5, nullable=True)
    dep: str = pa.Field(str_matches=r"^(?:\d{2,3}|2A|2B)$", nullable=True)
    com: str = pa.Field(str_matches=r"^(?:\d{2}|2A|2B)\d{3}$", nullable=True)
    agg: int = pa.Field(ge=1, le=2, nullable=True)
    int: int = pa.Field(ge=1, le=9, nullable=True)
    atm: int = pa.Field(ge=-1, le=9, ne=0, nullable=True)
    col: int = pa.Field(ge=-1, le=7, ne=0, nullable=True)
    adr: str = pa.Field(nullable=True)
    lat: str = pa.Field(str_matches=r"^\s*-?(?:[0-8]?\d|90),\d+$", nullable=True)
    long: str = pa.Field(
        str_matches=r"^\s*-?(?:1[0-7]\d|0?\d?\d|180),\d+$", nullable=True
    )

    class Config:
        name = "CaractSchema"
        coerce = True


class PlaceSchema(pa.DataFrameModel):
    Num_Acc: int = pa.Field(ge=200000000001, le=202699999999, unique=True)
    catr: int = pa.Field(ge=1, le=9, nullable=True)
    voie: str = pa.Field(nullable=True)
    v1: int = pa.Field(ge=-1, le=9, nullable=True)
    v2: str = pa.Field(str_matches=r"(?:\d{2}|[A-Z]|\s-)", nullable=True)
    circ: int = pa.Field(ge=-1, le=4, ne=0, nullable=True)
    nbv: int = pa.Field(ge=-1, nullable=True)
    vosp: int = pa.Field(ge=-1, le=3, nullable=True)
    prof: int = pa.Field(ge=-1, le=4, ne=0, nullable=True)
    pr: str = pa.Field(str_matches=r"^(?:-?\d+|\(\d+\))$", nullable=True)
    pr1: str = pa.Field(str_matches=r"^(?:-?\d+|\(\d+\))$", nullable=True)
    plan: int = pa.Field(ge=-1, le=4, ne=0, nullable=True)
    lartpc: str = pa.Field(str_matches=r"^(?:-1|\d+(?:,\d+)?)$", nullable=True)
    larrout: str = pa.Field(str_matches=r"^\s*(?:-1|\d+(?:,\d+)?)$", nullable=True)
    surf: int = pa.Field(ge=-1, le=9, ne=0, nullable=True)
    infra: int = pa.Field(ge=-1, le=9, nullable=True)
    situ: int = pa.Field(ge=-1, le=8, nullable=True)
    vma: int = pa.Field(ge=-1, le=1000, nullable=True)

    class Config:
        name = "PlaceSchema"
        coerce = True


class VehicleSchema(pa.DataFrameModel):
    Num_Acc: int = pa.Field(ge=200000000001, le=202699999999)
    id_vehicule: str = pa.Field(str_matches=r"^\d{3}.{1,2}\d{3}$", unique=True)
    num_veh: str = pa.Field(str_matches=r"^[A-Z\[\]]{1,2}\d{2}$")
    senc: int = pa.Field(ge=-1, le=3, nullable=True)
    catv: int = pa.Field(ge=-1, le=99, nullable=True)
    obs: int = pa.Field(ge=-1, le=17, nullable=True)
    obsm: int = pa.Field(ge=-1, le=9, nullable=True)
    choc: int = pa.Field(ge=-1, le=9, nullable=True)
    manv: int = pa.Field(ge=-1, le=26, nullable=True)
    motor: int = pa.Field(ge=-1, le=6, nullable=True)
    occutc: float = pa.Field(ge=0, nullable=True)

    class Config:
        name = "VehicleSchema"
        coerce = True
