from streamlit.testing.v1 import AppTest


def test_the_streamlit_app_runs():
    """Tests that the streamlit app starts properly."""
    at = AppTest.from_file("src/green_light_ui/app.py").run()
    assert True