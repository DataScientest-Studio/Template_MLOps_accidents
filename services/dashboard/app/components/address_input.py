"""Address input component for geocoding addresses."""
from __future__ import annotations

import streamlit as st

from .api_client import geocode_address

# Session state keys
ADDRESS_KEY = "address_input"
ADDRESS_SUGGESTIONS_KEY = "address_suggestions"
SELECTED_ADDRESS_KEY = "selected_address"
SELECTED_COORDS_KEY = "selected_coordinates"


def render_address_input() -> dict | None:
    """
    Render address input with autocomplete suggestions.

    Returns:
        Dict with address, latitude, longitude if address is selected, None otherwise
    """
    # Initialize session state
    if ADDRESS_KEY not in st.session_state:
        st.session_state[ADDRESS_KEY] = ""
    if ADDRESS_SUGGESTIONS_KEY not in st.session_state:
        st.session_state[ADDRESS_SUGGESTIONS_KEY] = []
    if SELECTED_ADDRESS_KEY not in st.session_state:
        st.session_state[SELECTED_ADDRESS_KEY] = None
    if SELECTED_COORDS_KEY not in st.session_state:
        st.session_state[SELECTED_COORDS_KEY] = None

    # Address input field (full width)
    address = st.text_input(
        "Address",
        value=st.session_state[ADDRESS_KEY],
        placeholder="Enter a full address",
        key="address_input_field",
        help="Enter a complete address and press Enter to geocode",
    )

    # Update session state when address changes
    if address != st.session_state[ADDRESS_KEY]:
        st.session_state[ADDRESS_KEY] = address
        st.session_state[SELECTED_ADDRESS_KEY] = None
        st.session_state[SELECTED_COORDS_KEY] = None

        # NOTE: Autocomplete suggestions disabled for Nominatim per their usage policy
        # Nominatim Usage Policy explicitly prohibits autocomplete search
        # Only attempt suggestions if we're using a provider that supports it (e.g., Google)
        # For now, we skip suggestions to comply with Nominatim policy
        st.session_state[ADDRESS_SUGGESTIONS_KEY] = []

    # Display suggestions (disabled for Nominatim compliance)
    suggestions = st.session_state[ADDRESS_SUGGESTIONS_KEY]
    # Note: Suggestions disabled - Nominatim Usage Policy prohibits autocomplete search

    # If address is entered but not selected from suggestions, try to geocode
    if (
        address
        and len(address) >= 3
        and st.session_state[SELECTED_COORDS_KEY] is None
        and not suggestions
    ):
        # Try to geocode the address
        with st.spinner("Geocoding address..."):
            result = geocode_address(address)
            if result:
                st.session_state[SELECTED_ADDRESS_KEY] = result.get("display_name", address)
                st.session_state[SELECTED_COORDS_KEY] = {
                    "latitude": result.get("latitude"),
                    "longitude": result.get("longitude"),
                }
                st.rerun()

    # Return selected coordinates if available
    if st.session_state[SELECTED_COORDS_KEY]:
        coords = st.session_state[SELECTED_COORDS_KEY]
        selected_address = st.session_state[SELECTED_ADDRESS_KEY] or address
        return {
            "address": selected_address,
            "latitude": coords["latitude"],
            "longitude": coords["longitude"],
        }

    return None
