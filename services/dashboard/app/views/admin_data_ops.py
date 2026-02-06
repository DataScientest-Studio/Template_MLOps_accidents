"""Admin Data Ops: trigger pipelines, view job logs."""

import streamlit as st

from ..components.api_client import get, post


def render():
    st.title("Data Ops")
    st.markdown("Trigger preprocessing and feature engineering; view job logs.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Run Preprocessing", type="primary"):
            resp = post("/api/v1/data/preprocess", json={})
            if resp is None:
                st.error("Not authenticated.")
            elif resp.status_code == 202:
                job = resp.json()
                st.session_state["data_ops_job_started"] = (
                    f"Job started: {job.get('job_id', '')}"
                )
            else:
                try:
                    st.error(resp.json().get("detail", "Failed"))
                except Exception:
                    st.error("Failed")
    with col2:
        if st.button("Run Feature Engineering", type="primary"):
            resp = post("/api/v1/data/build-features", json={})
            if resp is None:
                st.error("Not authenticated.")
            elif resp.status_code == 202:
                job = resp.json()
                st.session_state["data_ops_job_started"] = (
                    f"Job started: {job.get('job_id', '')}"
                )
            else:
                try:
                    st.error(resp.json().get("detail", "Failed"))
                except Exception:
                    st.error("Failed")

    st.markdown("---")

    expl_col1, expl_col2 = st.columns(2)
    with expl_col1:
        st.markdown("**Preprocessing**")
        st.caption(
            "Reads raw CSVs (usagers, caracteristiques, lieux, vehicules), validates and merges them, "
            "cleans columns and target, and writes **interim_dataset.csv** for feature engineering."
        )
    with expl_col2:
        st.markdown("**Feature engineering**")
        st.caption(
            "Loads interim_dataset.csv, builds temporal/cyclic and interaction features, "
            "encodes labels, and saves **features.csv** and **label_encoders.joblib** for training."
        )

    st.markdown("---")

    page_size = st.session_state.get("data_ops_page_size", 10)
    page = st.session_state.get("data_ops_page", 0)
    offset = page * page_size

    @st.fragment(run_every=4)
    def job_logs_section():
        st.subheader("Job logs")
        # Page size selector (persisted in session)
        col_size, col_nav = st.columns([1, 3])
        with col_size:
            new_size = st.selectbox(
                "Rows per page",
                options=[10, 20, 50, 100],
                index=[10, 20, 50, 100].index(page_size),
                key="data_ops_page_size_select",
            )
            if new_size != page_size:
                st.session_state["data_ops_page_size"] = new_size
                st.session_state["data_ops_page"] = 0
                st.rerun()

        st.markdown(
            """
            <style>
            div[data-testid="stExpander"] {
                border: none !important;
                box-shadow: none !important;
            }
            div[data-testid="stExpander"] > div {
                border: none !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        resp = get("/api/v1/data/jobs", params={"limit": page_size, "offset": offset})
        if resp is None:
            st.warning("Not authenticated.")
        elif resp.status_code != 200:
            st.error("Failed to load jobs.")
        else:
            data = resp.json()
            items = data.get("items") or []
            total = data.get("total", 0)
            if not items:
                st.info("No jobs yet.")
            else:
                for j in items:
                    msg = j.get("message") or ""
                    prog = j.get("progress")
                    prog_str = f" · {prog:.0f}%" if prog is not None else ""
                    line_text = (
                        f"{j.get('job_type', '')} | {j.get('status', '')} | "
                        f"{j.get('created_at', '')} | {j.get('job_id', '')}"
                        + (f" | {msg}{prog_str}" if msg or prog_str else "")
                    )
                    with st.expander(line_text, expanded=False):
                        if j.get("error"):
                            st.caption(f"**Error:** {j['error']}")
                        logs = j.get("logs") or []
                        if logs:
                            st.text("\n".join(logs))
                        result = j.get("result")
                        if result:
                            st.json(result)
                # Pagination nav
                num_pages = max(1, (total + page_size - 1) // page_size)
                st.caption(
                    f"Showing {offset + 1}–{min(offset + len(items), total)} of {total} jobs (newest first)"
                )
                prev_col, _, next_col = st.columns([1, 2, 1])
                with prev_col:
                    if page > 0 and st.button("← Previous", key="data_ops_prev"):
                        st.session_state["data_ops_page"] = page - 1
                        st.rerun()
                with next_col:
                    if page < num_pages - 1 and st.button(
                        "Next →", key="data_ops_next"
                    ):
                        st.session_state["data_ops_page"] = page + 1
                        st.rerun()

    job_logs_section()

    if st.session_state.get("data_ops_job_started"):
        st.success(st.session_state["data_ops_job_started"])
        del st.session_state["data_ops_job_started"]
