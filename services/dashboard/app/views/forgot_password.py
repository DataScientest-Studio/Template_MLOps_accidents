"""Forgot password: request reset token, then set new password (masked)."""

import streamlit as st

from ..auth import forgot_password, reset_password


def render():
    """Two-step flow: request reset by username, then reset with token + new password."""
    st.title("Reset password")
    st.markdown(
        "Request a password reset, then set a new password using the token you receive."
    )

    step = st.session_state.get("forgot_password_step", "request")

    if step == "request":
        with st.form("forgot_password_request"):
            username = st.text_input("Username", key="forgot_username")
            submitted = st.form_submit_button("Send reset")
        if submitted:
            if not username or len(username.strip()) < 3:
                st.error("Enter a valid username (at least 3 characters).")
            else:
                ok, result = forgot_password(username.strip())
                if not ok:
                    st.error(result)
                else:
                    reset_token = (
                        result.get("reset_token") if isinstance(result, dict) else None
                    )
                    st.warning(
                        "Email delivery is not yet implemented. Reset links are not sent by email."
                    )
                    if reset_token:
                        st.session_state["forgot_reset_token"] = reset_token
                        st.session_state["forgot_password_step"] = "reset"
                        st.success(
                            "Reset token generated (dev mode). Enter it below with your new password."
                        )
                        st.rerun()
                    else:
                        st.info(
                            "If an account exists, a reset link would be sent. Enable dev mode (DEV_PASSWORD_RESET_TOKEN_IN_RESPONSE) to receive the token here instead."
                        )

        st.markdown("---")
        if st.button("Back to login", key="forgot_back"):
            st.session_state.pop("show_forgot_password", None)
            st.session_state.pop("forgot_password_step", None)
            st.session_state.pop("forgot_reset_token", None)
            st.rerun()
        return

    # step == "reset"
    token_prefill = st.session_state.get("forgot_reset_token", "")
    with st.form("reset_password_form"):
        token = st.text_input(
            "Reset token", value=token_prefill, type="password", key="reset_token_input"
        )
        new_password = st.text_input(
            "New password", type="password", key="reset_new_password"
        )
        confirm = st.text_input(
            "Confirm new password", type="password", key="reset_confirm_password"
        )
        submitted = st.form_submit_button("Set new password")
    if submitted:
        if not token:
            st.error("Reset token is required.")
        elif not new_password or len(new_password) < 8:
            st.error("New password must be at least 8 characters.")
        elif new_password != confirm:
            st.error("Passwords do not match.")
        else:
            ok, err = reset_password(token, new_password)
            if not ok:
                st.error(err)
            else:
                st.success("Password updated. You can sign in with your new password.")
                st.session_state.pop("forgot_password_step", None)
                st.session_state.pop("forgot_reset_token", None)
                if st.button("Go to login", key="reset_done"):
                    st.session_state.pop("show_forgot_password", None)
                    st.rerun()

    st.markdown("---")
    if st.button("Back to login", key="reset_back"):
        st.session_state.pop("show_forgot_password", None)
        st.session_state.pop("forgot_password_step", None)
        st.session_state.pop("forgot_reset_token", None)
        st.rerun()
