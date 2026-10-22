"""Help & Customer Support — FAQ, bot, tickets."""

from __future__ import annotations

import streamlit as st

from services.customer_portal_store import (
    add_ticket_message,
    create_support_ticket,
    list_tickets_for_user,
)
from services.policy_bot_ui import render_policy_bot_chat
from services.portal_ui import portal_page_setup, status_badge
from services.role_dashboard import PAGE_SUPPORT
from services.support_faq import FAQ_ITEMS, TICKET_CATEGORIES
from services.portal_display import format_portal_datetime, ticket_why_raised_markdown
from services.ui_components import section_heading
from services.ui_copy import polish_ui_copy


def render() -> None:
    user_id = portal_page_setup(
        "Help & Customer Support",
        "FAQs, policy-aware bot, and simulated support tickets.",
        page_kind=PAGE_SUPPORT,
    )

    tab_faq, tab_bot, tab_tickets = st.tabs(["FAQ", "Support bot", "My tickets"])

    with tab_faq:
        section_heading("Frequently asked questions", variant="travel")
        for item in FAQ_ITEMS:
            with st.expander(polish_ui_copy(item["q"])):
                st.write(polish_ui_copy(item["a"]))

    with tab_bot:
        section_heading("Chat with support bot", variant="plan")
        st.caption(
            "For signup-gated chat with URL tools, open **Document Assistant** in the sidebar."
        )
        render_policy_bot_chat(
            user_id,
            session_key="support",
            show_intro=True,
            escalate_page_hint="the **My tickets** tab on this page",
            show_url_indexer=True,
        )

    with tab_tickets:
        section_heading("Submit a ticket", variant="travel")
        with st.form("new_ticket"):
            cat = st.selectbox("Category", TICKET_CATEGORIES)
            subj = st.text_input("Subject")
            body = st.text_area("Description", height=100)
            if st.form_submit_button("Create ticket"):
                if len(subj.strip()) < 3 or len(body.strip()) < 10:
                    st.error("Please add a subject and description.")
                else:
                    t = create_support_ticket(user_id, cat, subj.strip(), body.strip())
                    st.success(f"Ticket **{t['ticket_id']}** created.")
                    st.rerun()

        section_heading("Ticket list", variant="travel-sub")
        tickets = list_tickets_for_user(user_id)
        if not tickets:
            st.caption("No tickets yet.")
        for t in reversed(tickets):
            with st.expander(f"{t.get('ticket_id')} — {t.get('subject')}"):
                status_badge("Status", t.get("status", "Open"))
                st.caption(
                    f"Opened {format_portal_datetime(str(t.get('created_at', '')))}"
                )
                st.markdown("**Why you opened this ticket**")
                st.markdown(ticket_why_raised_markdown(t))
                st.divider()
                for msg in t.get("messages", []):
                    who = "You" if msg.get("from") == "user" else "Support"
                    st.markdown(f"**{who}:** {polish_ui_copy(msg.get('body', ''))}")
                with st.form(key=f"reply_{t['ticket_id']}"):
                    reply = st.text_input("Add a message")
                    if st.form_submit_button("Send"):
                        if reply.strip():
                            add_ticket_message(t["ticket_id"], user_id, reply.strip())
                            st.rerun()
                if t.get("category") in ("Refund Issue", "Account Restriction"):
                    if st.button("Request escalation", key=f"esc_{t['ticket_id']}"):
                        add_ticket_message(
                            t["ticket_id"],
                            user_id,
                            "Please escalate this case for manual review. "
                            "An admin will update the ticket status.",
                        )
                        st.rerun()


render()
