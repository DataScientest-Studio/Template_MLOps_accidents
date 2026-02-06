"""Admin User Management: list, add, delete users."""

import streamlit as st

from ..components.api_client import delete as api_delete
from ..components.api_client import get, post


def _format_api_error(detail) -> str:
    """Turn FastAPI/Pydantic error detail into a user-friendly message."""
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list):
        parts = []
        for item in detail:
            if not isinstance(item, dict):
                parts.append(str(item))
                continue
            loc = item.get("loc", [])
            msg = item.get("msg", "Invalid value")
            # loc is e.g. ['body', 'password'] or ['body', 'username']
            field = loc[-1] if len(loc) > 1 else (loc[0] if loc else "")
            if field:
                # Human-readable field name
                field_name = field.replace("_", " ").strip().capitalize()
                parts.append(f"**{field_name}**: {msg}")
            else:
                parts.append(msg)
        return " — ".join(parts) if parts else "Validation failed."
    return str(detail) if detail is not None else "Request failed."


def render():
    st.title("User Management")
    st.markdown("List, add, and delete users (admin only).")

    # List users
    st.subheader("Users")
    resp = get("/api/v1/auth/users")
    if resp is None:
        st.warning("Not authenticated.")
        return
    if resp.status_code != 200:
        st.error("Failed to load users.")
        return
    users = resp.json()
    if not users:
        st.info("No users.")
    else:
        for u in users:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.markdown(
                    f"**{u.get('username', '')}** | {u.get('role', '')} | {u.get('email', '')}"
                )
            with col3:
                uid = u.get("id")
                if uid and st.button("Delete", key=f"del_{uid}"):
                    r = api_delete(f"/api/v1/auth/users/{uid}")
                    if r and r.status_code == 204:
                        st.success("Deleted.")
                        st.rerun()
                    elif r:
                        try:
                            st.error(
                                _format_api_error(r.json().get("detail", "Failed"))
                            )
                        except Exception:
                            st.error("Failed")

    st.markdown("---")
    st.subheader("Add user")
    with st.form("add_user"):
        username = st.text_input("Username")
        password = st.text_input(
            "Password", type="password", autocomplete="new-password"
        )
        email = st.text_input("Email (optional)")
        full_name = st.text_input("Full name (optional)")
        role = st.selectbox("Role", ["user", "admin"])
        submitted = st.form_submit_button("Create user")
    if submitted:
        if len(username.strip()) < 3:
            st.error("Username must be at least 3 characters.")
        elif not password:
            st.error("Password is required.")
        elif len(password) < 8:
            st.warning("Password must be at least 8 characters.")
        elif username and password:
            r = post(
                "/api/v1/auth/users",
                json={
                    "username": username,
                    "password": password,
                    "email": email or None,
                    "full_name": full_name or None,
                    "role": role,
                },
            )
            if r and r.status_code == 200:
                st.success("User created.")
                st.rerun()
            elif r:
                try:
                    detail = r.json().get("detail", "Request failed.")
                    st.error(_format_api_error(detail))
                except Exception:
                    st.error("Request failed.")
