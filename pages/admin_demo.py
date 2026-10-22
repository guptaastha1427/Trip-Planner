"""Demo admin — account review and refund workflow (prototype only)."""

import streamlit as st

from services.admin_console import render_admin_console, render_admin_unlock_gate
from services.portal_ui import portal_page_setup


def render() -> None:
    portal_page_setup(
        "Admin",
        "Simulated back-office tools for training. Not secured for production.",
        show_page_strip=False,
    )
    st.warning("This page is illustrative only. No real authorization is enforced.")

    if not render_admin_unlock_gate():
        return

    render_admin_console(show_warning=False)


render()
