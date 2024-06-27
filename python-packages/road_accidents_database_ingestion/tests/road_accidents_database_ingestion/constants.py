from io import StringIO
from pathlib import Path

from road_accidents_database_ingestion.enums import RawRoadAccidentCsvFileNames

caracteristiques = """"Num_Acc";"jour";"mois";"an";"hrmn";"lum";"dep";"com";"agg";"int";"atm";"col";"adr";"lat";"long"
"202100000001";"30";"11";"2021";"07:32";"2";"30";"30319";"1";"1";"1";"1";"CD 981";"44,0389580000";"4,3480220000"
"""
lieux=""""Num_Acc";"catr";"voie";"v1";"v2";"circ";"nbv";"vosp";"prof";"pr";"pr1";"plan";"lartpc";"larrout";"surf";"infra";"situ";"vma"
"202100000001";"3";"981";" -1";"N/A";"2";"2";"0";"1";"(1)";"(1)";"1";"";" -1";"1";"0";"1";"80"
"""
usager=""""Num_Acc";"id_vehicule";"num_veh";"place";"catu";"grav";"sexe";"an_nais";"trajet";"secu1";"secu2";"secu3";"locp";"actp";"etatp"
"202100000001";"201Â 764";"B01";"1";"1";"3";"1";"2000";"1";"0";"9";" -1";"0";"0";" -1"
"""
vehicules=""""Num_Acc";"id_vehicule";"num_veh";"senc";"catv";"obs";"obsm";"choc";"manv";"motor";"occutc"
"202100000001";"201Â 764";"B01";"1";"1";"0";"2";"1";"1";"5";""
"""

# DF_CARAC, DF_PLACES,DF_USERS, DF_VEH=get_dataframes(caracteristiques_file=StringIO(caracteristiques),
#                                                      lieux_file=StringIO(lieux),
#                                                      usagers_file=StringIO(usager),
#                                                      vehicules_file=StringIO(vehicules))


def create_raw_road_accident_files_in_dir(path: Path, year: str="2021") -> None:
    with open(path / f"{RawRoadAccidentCsvFileNames.caracteristiques}-{year}.csv", 'w') as f:
        f.write(caracteristiques)
    with open(path / f"{RawRoadAccidentCsvFileNames.lieux}-{year}.csv", 'w') as f:
        f.write(lieux)
    with open(path / f"{RawRoadAccidentCsvFileNames.usagers}-{year}.csv", 'w') as f:
        f.write(usager)
    with open(path / f"{RawRoadAccidentCsvFileNames.vehicules}-{year}.csv", 'w') as f:
        f.write(vehicules)
