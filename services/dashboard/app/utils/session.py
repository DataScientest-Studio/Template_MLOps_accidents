"""Session state and expiry for dashboard."""

import streamlit as st

from ..auth import (
    EXPIRES_AT_KEY,
    TOKEN_KEY,
    USER_KEY,
    fetch_me,
    session_expired,
)


def clear_session():
    """Clear auth-related session state (logout)."""
    for key in (TOKEN_KEY, "refresh_token", EXPIRES_AT_KEY, USER_KEY):
        if key in st.session_state:
            del st.session_state[key]


def ensure_authenticated() -> bool:
    """
    Check token presence and expiry; optionally refresh user from API.
    Returns True if authenticated, False otherwise (caller should redirect to login).
    """
    token = st.session_state.get(TOKEN_KEY)
    if not token:
        return False
    expires_at = st.session_state.get(EXPIRES_AT_KEY, 0)
    if session_expired(expires_at):
        clear_session()
        return False
    if USER_KEY not in st.session_state:
        user = fetch_me(token)
        if not user:
            clear_session()
            return False
        st.session_state[USER_KEY] = user
    return True
