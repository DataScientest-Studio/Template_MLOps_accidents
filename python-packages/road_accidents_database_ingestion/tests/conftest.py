import shutil
from pathlib import Path

import pytest

@pytest.fixture()
def temp_dir(tmpdir_factory):
    """Creates a temp dir and deletes it along with all its files."""
    my_tmpdir = tmpdir_factory.mktemp("data")
    yield Path(my_tmpdir)
    shutil.rmtree(str(my_tmpdir))
