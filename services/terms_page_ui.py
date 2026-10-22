"""Shared tabbed layout for Terms & Conditions (presentation only)."""

from __future__ import annotations

import streamlit as st

from services.support_faq import policy_summary_markdown
from services.travel_packages import (
    build_travel_package_catalog_footer_markdown,
    catalog_rows_for_ui,
)
from services.terms_content import (
    RAG_ASSISTANT_SECTION_TITLES,
    RAG_CHAT_TERMS_INTRO,
    RAG_CHAT_TERMS_SECTIONS,
    RAG_CHAT_TOC,
    TERMS_INTRO,
    TERMS_PACKAGES_SECTION_TITLES,
    TERMS_PLATFORM_SECTION_TITLES,
    TERMS_SECTIONS,
    TERMS_TABLE_OF_CONTENTS,
)
from services.ui_components import section_heading
from services.ui_copy import polish_ui_copy


def _sections_by_titles(titles: tuple[str, ...]) -> list[tuple[str, str]]:
    title_set = set(titles)
    return [(t, b) for t, b in RAG_CHAT_TERMS_SECTIONS if t in title_set]


_CATALOG_SECTION_TITLE = "Travel package catalog & fare types (demo)"


def _render_terms_section_body(title: str, body: str) -> None:
    if title == _CATALOG_SECTION_TITLE:
        st.markdown(
            polish_ui_copy(
                "### Catalog packages (illustrative INR pricing)\n\n"
                    "**Five bundles only** — each is **1 Night / 1 Day** (depart Day 1, overnight, return Day 2)."
            )
        )
        st.dataframe(catalog_rows_for_ui(), width="stretch", hide_index=True)
        st.markdown(polish_ui_copy(build_travel_package_catalog_footer_markdown()))
        return
    st.markdown(polish_ui_copy(body.strip()))


def _render_section_list(sections: list[tuple[str, str]], variant: str = "travel-sub") -> None:
    for title, body in sections:
        section_heading(title, variant=variant)
        _render_terms_section_body(title, body)


def render_comprehensive_terms(*, show_platform_intro: bool = True) -> None:
    """
    Tabbed Terms & Conditions — accessible without blocking signup or chat elsewhere.
    """
    if show_platform_intro:
        st.markdown(polish_ui_copy(TERMS_INTRO))
        st.caption(
            "Tabs cover **app overview**, **why choose us**, **packages & subscription tiers**, "
            "RAG rules, and bookings/refunds. Indexed for the **Document Assistant** bot."
        )

    tab_overview, tab_rag, tab_packages, tab_legal = st.tabs(
        [
            "Overview & why us",
            "Document Assistant (RAG)",
            "Packages & tiers",
            "Bookings, refunds & legal",
        ]
    )

    with tab_overview:
        section_heading("Platform at a glance", variant="travel")
        _render_section_list(_sections_by_titles(TERMS_PLATFORM_SECTION_TITLES))

    with tab_rag:
        st.markdown(polish_ui_copy(RAG_CHAT_TERMS_INTRO))
        with st.expander("Section index — Document Assistant", expanded=False):
            for i, title in enumerate(RAG_CHAT_TOC, 1):
                st.markdown(f"{i}. {polish_ui_copy(title)}")
        section_heading("RAG chatbot policies", variant="plan")
        _render_section_list(_sections_by_titles(RAG_ASSISTANT_SECTION_TITLES))

    with tab_packages:
        section_heading("Commercial & catalog terms (demo)", variant="travel")
        _render_section_list(_sections_by_titles(TERMS_PACKAGES_SECTION_TITLES))

    with tab_legal:
        with st.expander("Section index — Bookings, refunds & portal", expanded=False):
            for i, title in enumerate(TERMS_TABLE_OF_CONTENTS, 1):
                st.markdown(f"{i}. {polish_ui_copy(title)}")
        section_heading("Policy comparison", variant="travel")
        st.caption("Ticket and package policies used by the refund rule engine.")
        st.markdown(polish_ui_copy(policy_summary_markdown()))
        section_heading("Full terms & policies", variant="travel")
        for title, body in TERMS_SECTIONS:
            section_heading(title, variant="travel-sub")
            _render_terms_section_body(title, body)
