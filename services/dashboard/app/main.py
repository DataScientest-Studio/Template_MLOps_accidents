"""Streamlit dashboard entry: auth check, then Control Center or login."""

import streamlit as st
from app.auth import USER_KEY, is_admin
from app.components.sidebar import PAGE_KEY, render_sidebar
from app.utils.session import ensure_authenticated
from app.views.admin_data_ops import render as render_data_ops
from app.views.admin_ml_ops import render as render_ml_ops
from app.views.admin_user_mgmt import render as render_user_mgmt
from app.views.forgot_password import render as render_forgot_password
from app.views.login import render_login
from app.views.user_prediction import render as render_prediction

st.set_page_config(
    page_title="Accident Severity Dashboard",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Hide "Show password" eye icon globally so passwords are never revealed
st.markdown(
    """
    <style>
    [data-testid="stTextInput"] button[title="Show password text"],
    [data-testid="stTextInput"] button[aria-label="Show password text"] {
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if not ensure_authenticated():
    if st.session_state.get("show_forgot_password"):
        render_forgot_password()
    else:
        render_login()
else:
    render_sidebar()
    page = st.session_state.get(PAGE_KEY, "prediction")
    user = st.session_state.get(USER_KEY, {})
    role = user.get("role", "")
    if page == "data_ops" and is_admin(role):
        render_data_ops()
    elif page == "ml_ops" and is_admin(role):
        render_ml_ops()
    elif page == "user_mgmt" and is_admin(role):
        render_user_mgmt()
    else:
        st.session_state[PAGE_KEY] = "prediction"
        render_prediction()
