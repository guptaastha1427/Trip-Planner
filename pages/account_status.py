"""Account Status & Policy Violations."""

import streamlit as st

from services.customer_portal_store import (
    effective_account_profile,
    get_portal_state,
    submit_appeal,
)
from services.demo_users import account_status_label
from services.portal_ui import portal_page_setup, status_badge
from services.role_dashboard import PAGE_ACCOUNT
from services.ui_components import section_heading


def render() -> None:
    user_id = portal_page_setup(
        "Account Status & Policy Violations",
        "View restriction types, violation reasons, and submit an appeal.",
        page_kind=PAGE_ACCOUNT,
    )
    profile = effective_account_profile(user_id)
    status = profile.get("account_status", "active")
    status_badge("Account", account_status_label(status))

    section_heading("Restriction details", variant="travel")
    notes = profile.get("restriction_notes") or []
    if not notes:
        st.success("No active restrictions on this account.")
    else:
        for n in notes:
            with st.container(border=True):
                st.markdown(f"**{n.get('code', 'notice').replace('_', ' ').title()}**")
                st.write(n.get("summary", ""))
                st.caption(f"Date: {n.get('date', '—')} · Ref: {n.get('booking_ref') or '—'}")

    section_heading("Appeal", variant="refine")
    st.caption(
        "A refund rejection alone does not blacklist an account. "
        "Appeals are for documented restrictions."
    )
    with st.form("appeal_form"):
        msg = st.text_area("Why should we review your account status?", height=120)
        if st.form_submit_button("Submit appeal"):
            if len(msg.strip()) < 10:
                st.error("Please provide a short explanation (10+ characters).")
            else:
                ap = submit_appeal(user_id, msg.strip())
                st.success(f"Appeal submitted: **{ap['appeal_id']}** (review queue).")

    section_heading("Your appeals", variant="travel-sub")
    appeals = [a for a in get_portal_state().get("account_appeals", []) if a.get("user_id") == user_id]
    for a in reversed(appeals):
        st.markdown(f"**{a.get('appeal_id')}** — {a.get('status')} — {a.get('created_at', '')[:10]}")
        st.caption(a.get("message", ""))

    section_heading("Support options", variant="travel-sub")
    st.markdown(
        "- Open **Help & Customer Support** → category *Account Restriction*\n"
        "- Escalate disputed refund decisions with category *Refund Issue*"
    )


render()
