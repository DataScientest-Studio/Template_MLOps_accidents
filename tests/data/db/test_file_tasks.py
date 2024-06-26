import pytest

from src.data.db.file_tasks import (
    validate_road_accident_files_are_the_expected_ones,
    get_road_accident_file2model,
)
from src.data.db.enum import RawRoadAccidentCsvFileNames
import tests.data.db.constants as c


def test_validate_road_accident_files_are_the_expected_ones_should_pass(temp_dir):
    c.create_raw_road_accident_files_in_dir(temp_dir)
    assert validate_road_accident_files_are_the_expected_ones(list(temp_dir.glob("*")))


def test_check_if_files_are_the_expected_ones_should_raise_one_missing_file(temp_dir):
    """Tests that function should raise because a csv road accident file is missing."""
    c.create_raw_road_accident_files_in_dir(temp_dir)
    # delete one road accident file
    files = temp_dir.glob("*")
    next(files).unlink()
    with pytest.raises(FileNotFoundError):
        validate_road_accident_files_are_the_expected_ones(list(temp_dir.glob("*")))


def test_get_road_accident_file2model(temp_dir):
    c.create_raw_road_accident_files_in_dir(temp_dir)
    file_stats = get_road_accident_file2model(temp_dir)
    assert not set(RawRoadAccidentCsvFileNames).symmetric_difference(set(file_stats))
