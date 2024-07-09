from pathlib import Path
from streamlit.testing.v1 import AppTest


def test_the_streamlit_app_runs():
    """Tests that the streamlit app starts properly."""
    current_path = Path(__file__).parent
    project_path = current_path.parent
    at = AppTest.from_file(str(project_path / "src" / "green_light_ui" / "app.py")).run()
    assert True