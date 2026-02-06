"""Login view: form and redirect on success."""

import time

import streamlit as st

from ..auth import (
    EXPIRES_AT_KEY,
    REFRESH_KEY,
    TOKEN_KEY,
    USER_KEY,
    login,
)
from ..config import SESSION_EXPIRE_MINUTES


def render_login():
    """Show login form; on success store token and user, then rerun to show app."""
    st.title("Accident Severity Dashboard")
    st.markdown("Sign in to access the Control Center.")
    with st.form("login_form"):
        username = st.text_input("Username", key="login_username")
        password = st.text_input(
            "Password",
            type="password",
            key="login_password",
            autocomplete="current-password",
        )
        submitted = st.form_submit_button("Sign in")
    st.markdown("---")
    if st.button("Forgot password?", key="login_forgot"):
        st.session_state["show_forgot_password"] = True
        st.rerun()
    if not submitted:
        return
    if not username or not password:
        st.error("Username and password are required.")
        return
    ok, result = login(username, password)
    if not ok:
        st.error(result)
        return
    # result is { access_token, refresh_token?, expires_in }
    st.session_state[TOKEN_KEY] = result.get("access_token", "")
    st.session_state[REFRESH_KEY] = result.get("refresh_token") or ""
    expires_in = result.get("expires_in", SESSION_EXPIRE_MINUTES * 60)
    st.session_state[EXPIRES_AT_KEY] = time.time() + expires_in
    # Fetch user for role
    from ..auth import fetch_me

    user = fetch_me(st.session_state[TOKEN_KEY])
    if user:
        st.session_state[USER_KEY] = user
    st.success("Signed in.")
    st.rerun()
