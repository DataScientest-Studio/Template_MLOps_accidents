"""Control Center: prediction form, map, result."""

from __future__ import annotations

import folium
import streamlit as st
from streamlit_folium import st_folium

from ..components.api_client import post, check_geocode_health
from ..components.prediction_form import render_prediction_form, render_current_coordinates_display, KEY_PREFIX
from ..components.address_input import render_address_input


def render():
    st.title("Control Center — Accident Severity")
    st.markdown("Enter incident details and get severity prediction.")

    # Check if geocoding service is available
    geocoding_available = check_geocode_health()

    # Create two-column layout: Location/Coordinates (left) | Map (right)
    col_left, col_right = st.columns([1, 1])

    address_coords = None
    
    with col_left:
        # Location section
        st.markdown("### Location")
        if geocoding_available:
            address_coords = render_address_input()
            if address_coords:
                st.info(f"📍 **Selected:** {address_coords.get('address', 'Unknown address')}")
        else:
            st.warning("⚠️ Geocoding service is currently unavailable. Click on the map to set coordinates.")
        
        # Add vertical space to push coordinates to bottom (aligning with map bottom)
        # Using empty containers to create flexible spacing
        spacer_container = st.empty()
        with spacer_container.container():
            for _ in range(8):  # Creates approximately 200px of space
                st.write("")
        
        # Current Coordinates Display (at bottom, aligned with map)
        render_current_coordinates_display(address_coords, geocoding_available)

    with col_right:
        # Map display (always shown, spans over two rows)
        st.markdown("### Map")
        
        # Get current coordinates from session state (updated by geocoding or map click)
        current_lat = st.session_state.get(f"{KEY_PREFIX}lat", 48.60)
        current_long = st.session_state.get(f"{KEY_PREFIX}long", 2.89)
        
        # Create map with current coordinates
        m = folium.Map(location=[current_lat, current_long], zoom_start=17)
        
        # Add draggable marker
        marker_popup_text = address_coords.get("address", "Click map to set location") if address_coords else "Click map to set location"
        marker = folium.Marker(
            [current_lat, current_long],
            tooltip="Incident Location (drag marker or click map to move)",
            popup=marker_popup_text,
            draggable=True,
        )
        marker.add_to(m)
        
        # Render map and capture interactions
        map_data = st_folium(
            m,
            width=None,
            height=500,
            key="address_map",
            returned_objects=["last_object_clicked", "last_clicked"],
        )
        
        # Attribution required by Nominatim Usage Policy (below map)
        st.caption(
            "📍 Geocoding data © OpenStreetMap contributors, licensed under ODbL. "
            "See https://www.openstreetmap.org/copyright"
        )
        
        # Handle map interactions: marker drag or map click
        coordinates_updated = False
        
        # Check if marker was dragged/clicked
        if map_data.get("last_object_clicked"):
            clicked = map_data["last_object_clicked"]
            if clicked and isinstance(clicked, dict):
                if "lat" in clicked and "lng" in clicked:
                    new_lat = float(clicked["lat"])
                    new_long = float(clicked["lng"])
                    # Only update if coordinates actually changed
                    if abs(new_lat - current_lat) > 0.0001 or abs(new_long - current_long) > 0.0001:
                        st.session_state[f"{KEY_PREFIX}lat"] = new_lat
                        st.session_state[f"{KEY_PREFIX}long"] = new_long
                        coordinates_updated = True
        
        # Check if map was clicked (not marker)
        if not coordinates_updated and map_data.get("last_clicked"):
            clicked = map_data["last_clicked"]
            if clicked and isinstance(clicked, dict):
                if "lat" in clicked and "lng" in clicked:
                    new_lat = float(clicked["lat"])
                    new_long = float(clicked["lng"])
                    # Only update if coordinates actually changed
                    if abs(new_lat - current_lat) > 0.0001 or abs(new_long - current_long) > 0.0001:
                        st.session_state[f"{KEY_PREFIX}lat"] = new_lat
                        st.session_state[f"{KEY_PREFIX}long"] = new_long
                        coordinates_updated = True
        
        # Rerun if coordinates were updated
        if coordinates_updated:
            st.rerun()

    st.markdown("---")

    # Prediction form with address coordinates (full width below)
    features = render_prediction_form(
        address_coords=address_coords,
        geocoding_available=geocoding_available,
    )

    # Initialize session state for prediction results if not exists
    if "prediction_result" not in st.session_state:
        st.session_state.prediction_result = None
    if "prediction_features" not in st.session_state:
        st.session_state.prediction_features = None

    if st.button("Predict", type="primary"):
        resp = post("/api/v1/predict/", json={"features": features})
        if resp is None:
            st.error("Not authenticated.")
            st.session_state.prediction_result = None
            st.session_state.prediction_features = None
            return
        if resp.status_code != 200:
            try:
                detail = resp.json().get("detail", "Prediction failed")
            except Exception:
                detail = "Prediction failed"
            st.error(detail)
            st.session_state.prediction_result = None
            st.session_state.prediction_features = None
            return
        data = resp.json()
        pred = data.get("prediction")
        prob = data.get("probability", 0.0)
        model_type = data.get("model_type", "")
        severity_label = "Severe (1)" if pred == 1 else "Not severe (0)"
        # Store results in session state
        st.session_state.prediction_result = {
            "prediction": pred,
            "probability": prob,
            "model_type": model_type,
            "severity_label": severity_label,
        }
        st.session_state.prediction_features = features.copy()

    # Display results from session state (persists across reruns)
    if st.session_state.prediction_result is not None:
        result = st.session_state.prediction_result
        st.success(
            f"**Severity:** {result['severity_label']}  |  **Risk probability:** {result['probability']:.2%}  |  Model: {result['model_type']}"
        )
        if (
            st.session_state.prediction_features
            and "lat" in st.session_state.prediction_features
            and "long" in st.session_state.prediction_features
        ):
            # Street-level detail for prediction result map as well
            m = folium.Map(
                location=[
                    float(st.session_state.prediction_features["lat"]),
                    float(st.session_state.prediction_features["long"]),
                ],
                zoom_start=17,
            )
            folium.Marker(
                [
                    float(st.session_state.prediction_features["lat"]),
                    float(st.session_state.prediction_features["long"]),
                ],
                tooltip="Incident",
            ).add_to(m)
            st_folium(m, width=700, height=400)
