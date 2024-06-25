import shutil
from pathlib import Path

import pytest

from src.data.db.file_tasks import check_if_files_are_the_expected_ones, get_files
from src.data.db.enum import RawRoadAccidentCsvFileNames
import  tests.data.db.constants as c

@pytest.fixture()
def temp_dir(tmpdir_factory):
    my_tmpdir = tmpdir_factory.mktemp("data")
    yield Path(my_tmpdir)
    shutil.rmtree(str(my_tmpdir))

def test_check_if_files_are_the_expected_ones_should_pass(temp_dir):
    with open(temp_dir / f"{RawRoadAccidentCsvFileNames.caracteristiques}-2021.csv", 'w') as f:
        f.write(c.caracteristiques)
    with open(temp_dir / f"{RawRoadAccidentCsvFileNames.lieux}-2021.csv", 'w') as f:
        f.write(c.lieux)
    with open(temp_dir / f"{RawRoadAccidentCsvFileNames.usagers}-2021.csv", 'w') as f:
        f.write(c.usager)
    with open(temp_dir / f"{RawRoadAccidentCsvFileNames.vehicules}-2021.csv", 'w') as f:
        f.write(c.vehicules)
    assert check_if_files_are_the_expected_ones(temp_dir)

def test_check_if_files_are_the_expected_ones_should_raise_one_random_file(temp_dir):
    with open(temp_dir / f"{RawRoadAccidentCsvFileNames.caracteristiques}-2021.csv", 'w') as f:
        f.write(c.caracteristiques)
    with open(temp_dir / f"{RawRoadAccidentCsvFileNames.lieux}-2021.csv", 'w') as f:
        f.write(c.lieux)
    with open(temp_dir / f"{RawRoadAccidentCsvFileNames.usagers}-2021.csv", 'w') as f:
        f.write(c.usager)
    with open(temp_dir / f"random_name-2021.csv", 'w') as f:
        f.write(c.vehicules)
    with pytest.raises(FileNotFoundError):
        check_if_files_are_the_expected_ones(temp_dir)

def test_check_if_files_are_the_expected_ones_should_raise_one_missing_file(temp_dir):
    with open(temp_dir / f"{RawRoadAccidentCsvFileNames.caracteristiques}-2021.csv", 'w') as f:
        f.write(c.caracteristiques)
    with open(temp_dir / f"{RawRoadAccidentCsvFileNames.lieux}-2021.csv", 'w') as f:
        f.write(c.lieux)
    with open(temp_dir / f"{RawRoadAccidentCsvFileNames.usagers}-2021.csv", 'w') as f:
        f.write(c.usager)
    with pytest.raises(FileNotFoundError):
        check_if_files_are_the_expected_ones(temp_dir)

def test_get_files(temp_dir):
    with open(temp_dir / f"{RawRoadAccidentCsvFileNames.caracteristiques}-2021.csv", 'w') as f:
        f.write(c.caracteristiques)
    with open(temp_dir / f"{RawRoadAccidentCsvFileNames.lieux}-2021.csv", 'w') as f:
        f.write(c.lieux)
    with open(temp_dir / f"{RawRoadAccidentCsvFileNames.usagers}-2021.csv", 'w') as f:
        f.write(c.usager)
    with open(temp_dir / f"{RawRoadAccidentCsvFileNames.vehicules}-2021.csv", 'w') as f:
        f.write(c.vehicules)

    file_stats = get_files(temp_dir)
    assert not set(RawRoadAccidentCsvFileNames).symmetric_difference(set(file_stats))