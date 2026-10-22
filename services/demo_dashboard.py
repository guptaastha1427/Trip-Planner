"""Demo switch between customer (user) and back-office (admin) views — prototype only."""

from __future__ import annotations

import streamlit as st

DEMO_MODE_USER = "user"
DEMO_MODE_ADMIN = "admin"


def get_demo_dashboard_mode() -> str:
    if "demo_dashboard" not in st.session_state:
        st.session_state.demo_dashboard = DEMO_MODE_USER
    return str(st.session_state.demo_dashboard)


def is_admin_dashboard_mode() -> bool:
    return get_demo_dashboard_mode() == DEMO_MODE_ADMIN


def render_demo_dashboard_switch() -> None:
    """Sidebar control shown on every page (call from app.main before navigation)."""
    current = get_demo_dashboard_mode()
    st.sidebar.markdown("**Dashboard**")
    picked = st.sidebar.radio(
        "View as",
        options=[DEMO_MODE_USER, DEMO_MODE_ADMIN],
        index=0 if current == DEMO_MODE_USER else 1,
        format_func=lambda m: "👤 User" if m == DEMO_MODE_USER else "🔧 Admin",
        horizontal=True,
        key="_demo_dashboard_radio",
        label_visibility="collapsed",
    )
    if picked != current:
        st.session_state.demo_dashboard = picked
        if picked == DEMO_MODE_ADMIN:
            st.session_state.admin_unlocked = True
        _navigate_for_mode(picked)
        st.rerun()

    if is_admin_dashboard_mode():
        st.sidebar.caption("Back-office — refund queue & account tools.")
    else:
        st.sidebar.caption("Customer view — trips, bookings & support.")
    st.sidebar.divider()


def _navigate_for_mode(mode: str) -> None:
    try:
        import app as trip_app

        if mode == DEMO_MODE_ADMIN:
            st.switch_page(trip_app.ADMIN_PAGE)
        else:
            st.switch_page(trip_app.TRIP_PLANNER_PAGE)
    except Exception:
        pass
