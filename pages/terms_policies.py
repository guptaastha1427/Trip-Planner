"""Terms & Conditions & Policies."""

import streamlit as st

from services.portal_ui import portal_page_setup
from services.role_dashboard import PAGE_TERMS
from services.terms_page_ui import render_comprehensive_terms
from services.ui_components import section_heading
from services.ui_copy import polish_ui_copy


def render() -> None:
    portal_page_setup(
        "Terms & Conditions & Policies",
        "Overview, RAG assistant rules, packages, tiers, bookings, refunds, and legal notices.",
        page_kind=PAGE_TERMS,
    )
    section_heading("Terms & Conditions", variant="travel")
    st.markdown(
        polish_ui_copy(
            "Professional notice for the Trip Planner, **Document & Policy Assistant (RAG)**, "
            "demo bookings, and support. **Sign up** and **Chat** stay under **Document Assistant** "
            "in the sidebar — reading Terms here does not interrupt those flows."
        )
    )
    st.page_link(
        "pages/document_assistant.py",
        label="Open Document Assistant (sign up & chat)",
        icon="📄",
    )
    render_comprehensive_terms(show_platform_intro=True)


render()
