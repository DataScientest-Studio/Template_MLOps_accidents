"""Prediction form: inputs for accident features, returns dict for API."""

from __future__ import annotations

import streamlit as st
from streamlit_folium import st_folium
import folium

# Defaults aligned with src/models/test_features.json
DEFAULTS = {
    "place": 10,
    "catu": 3,
    "sexe": 1,
    "secu1": 0.0,
    "year_acc": 2021,
    "an_nais": 1961,
    "catv": 2,
    "obsm": 1,
    "motor": 1,
    "catr": 3,
    "circ": 2,
    "surf": 1,
    "situ": 1,
    "vma": 50,
    "lum": 5,
    "dep": 77,
    "com": 77317,
    "agg_": 2,
    "int": 1,
    "atm": 0,
    "col": 6,
    "lat": 48.60,
    "long": 2.89,
    "nb_victim": 2,
    "nb_vehicules": 1,
    "locp": 0,
    "actp": 0,
    "etatp": 0,
    "obs": 0,
    "v1": 0,
    "vosp": 0,
    "prof": 0,
    "plan": 0,
    "larrout": 0.0,
    "infra": 0,
}

KEY_PREFIX = "pred_"

# Export for use in other modules
__all__ = ["render_prediction_form", "render_current_coordinates_display", "KEY_PREFIX", "DEFAULTS"]


def render_current_coordinates_display(
    address_coords: dict | None = None,
    geocoding_available: bool = True,
) -> tuple[float, float]:
    """
    Display current coordinates (read-only) and initialize session state.
    
    Coordinates can be set via:
    - Address geocoding (if available)
    - Map click interaction
    
    Args:
        address_coords: Optional dict with latitude and longitude from address geocoding
        geocoding_available: Whether geocoding service is available
        
    Returns:
        Tuple of (latitude, longitude) values
    """
    # Determine default lat/long values
    default_lat = float(address_coords.get("latitude", DEFAULTS["lat"])) if address_coords else float(DEFAULTS["lat"])
    default_long = float(address_coords.get("longitude", DEFAULTS["long"])) if address_coords else float(DEFAULTS["long"])

    # Initialize session state if not set
    if f"{KEY_PREFIX}lat" not in st.session_state:
        st.session_state[f"{KEY_PREFIX}lat"] = default_lat
    if f"{KEY_PREFIX}long" not in st.session_state:
        st.session_state[f"{KEY_PREFIX}long"] = default_long

    # Update session state with geocoded coordinates if available
    if address_coords and address_coords.get("latitude") and address_coords.get("longitude"):
        geocoded_lat = float(address_coords["latitude"])
        geocoded_long = float(address_coords["longitude"])
        st.session_state[f"{KEY_PREFIX}lat"] = geocoded_lat
        st.session_state[f"{KEY_PREFIX}long"] = geocoded_long

    # Display current coordinates (read-only) - no heading
    current_lat = st.session_state.get(f"{KEY_PREFIX}lat", default_lat)
    current_long = st.session_state.get(f"{KEY_PREFIX}long", default_long)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Latitude", f"{current_lat:.6f}")
    with col2:
        st.metric("Longitude", f"{current_long:.6f}")
    
    st.caption("💡 Click on the map to set coordinates")
    
    return current_lat, current_long


def render_prediction_form(
    address_coords: dict | None = None,
    geocoding_available: bool = True,
) -> dict:
    """
    Render inputs and return current feature dict for POST /api/v1/predict/.
    Call when user clicks Predict; dict is built from current widget values.

    Args:
        address_coords: Optional dict with latitude and longitude from address geocoding
        geocoding_available: Whether geocoding service is available (shows/hides fallback)

    Returns:
        Dict of feature values for prediction API
    """
    st.subheader("Incident details")

    # Get lat/long from session state (updated by manual coordinates fallback or geocoding)
    default_lat = float(address_coords.get("latitude", DEFAULTS["lat"])) if address_coords else float(DEFAULTS["lat"])
    default_long = float(address_coords.get("longitude", DEFAULTS["long"])) if address_coords else float(DEFAULTS["long"])
    lat = float(st.session_state.get(f"{KEY_PREFIX}lat", default_lat))
    long = float(st.session_state.get(f"{KEY_PREFIX}long", default_long))

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        dep = st.number_input("Department (dep)", value=DEFAULTS["dep"], min_value=1, max_value=99, key=f"{KEY_PREFIX}dep")
        com = st.number_input("Commune (com)", value=DEFAULTS["com"], min_value=1000, key=f"{KEY_PREFIX}com")
    with c2:
        jour = st.number_input(
            "Day (jour)", value=7, min_value=1, max_value=31, key=f"{KEY_PREFIX}jour"
        )
        mois = st.number_input(
            "Month (mois)", value=12, min_value=1, max_value=12, key=f"{KEY_PREFIX}mois"
        )
        an = st.number_input(
            "Year (an)",
            value=2021,
            min_value=2015,
            max_value=2030,
            key=f"{KEY_PREFIX}an",
        )
        hrmn_str = st.text_input("Time (HH:MM)", value="17:00", key=f"{KEY_PREFIX}hrmn")
    st.markdown("---")
    c3, c4 = st.columns(2)
    with c3:
        place = st.number_input(
            "Place",
            value=DEFAULTS["place"],
            min_value=1,
            max_value=20,
            key=f"{KEY_PREFIX}place",
        )
        catu = st.number_input(
            "User category (catu)",
            value=DEFAULTS["catu"],
            min_value=1,
            max_value=5,
            key=f"{KEY_PREFIX}catu",
        )
        sexe = st.selectbox(
            "Sex (sexe)",
            options=[1, 2],
            format_func=lambda x: "Male" if x == 1 else "Female",
            key=f"{KEY_PREFIX}sexe",
        )
        an_nais = st.number_input(
            "Birth year (an_nais)",
            value=DEFAULTS["an_nais"],
            min_value=1920,
            max_value=2010,
            key=f"{KEY_PREFIX}an_nais",
        )
        catv = st.number_input(
            "Vehicle category (catv)",
            value=DEFAULTS["catv"],
            min_value=0,
            max_value=20,
            key=f"{KEY_PREFIX}catv",
        )
    with c4:
        vma = st.number_input(
            "Speed limit (vma)",
            value=DEFAULTS["vma"],
            min_value=0,
            max_value=150,
            key=f"{KEY_PREFIX}vma",
        )
        nb_victim = st.number_input(
            "Nb victims",
            value=DEFAULTS["nb_victim"],
            min_value=0,
            key=f"{KEY_PREFIX}nb_victim",
        )
        nb_vehicules = st.number_input(
            "Nb vehicles",
            value=DEFAULTS["nb_vehicules"],
            min_value=0,
            key=f"{KEY_PREFIX}nb_vehicules",
        )
        catr = st.number_input(
            "Road category (catr)",
            value=DEFAULTS["catr"],
            min_value=1,
            max_value=9,
            key=f"{KEY_PREFIX}catr",
        )
        circ = st.number_input(
            "Traffic (circ)",
            value=DEFAULTS["circ"],
            min_value=1,
            max_value=4,
            key=f"{KEY_PREFIX}circ",
        )
    hrmn = hrmn_str if (":" in hrmn_str and len(hrmn_str) <= 5) else "17:00"
    return {
        "place": place,
        "catu": catu,
        "sexe": sexe,
        "secu1": DEFAULTS["secu1"],
        "year_acc": an,
        "an_nais": an_nais,
        "catv": catv,
        "obsm": DEFAULTS["obsm"],
        "motor": DEFAULTS["motor"],
        "catr": catr,
        "circ": circ,
        "surf": DEFAULTS["surf"],
        "situ": DEFAULTS["situ"],
        "vma": vma,
        "jour": jour,
        "mois": mois,
        "an": an,
        "hrmn": hrmn,
        "lum": DEFAULTS["lum"],
        "dep": dep,
        "com": com,
        "agg_": DEFAULTS["agg_"],
        "int": DEFAULTS["int"],
        "atm": DEFAULTS["atm"],
        "col": DEFAULTS["col"],
        "lat": lat,
        "long": long,
        "nb_victim": nb_victim,
        "nb_vehicules": nb_vehicules,
        "locp": DEFAULTS["locp"],
        "actp": DEFAULTS["actp"],
        "etatp": DEFAULTS["etatp"],
        "obs": DEFAULTS["obs"],
        "v1": DEFAULTS["v1"],
        "vosp": DEFAULTS["vosp"],
        "prof": DEFAULTS["prof"],
        "plan": DEFAULTS["plan"],
        "larrout": DEFAULTS["larrout"],
        "infra": DEFAULTS["infra"],
    }
