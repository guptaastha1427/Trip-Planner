"""Interactive demo admin console — refunds, tickets, accounts, audit."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import streamlit as st

from services.customer_portal_store import (
    ADMIN_TICKET_STATUSES,
    admin_set_account_status,
    admin_update_ticket,
    append_audit,
    effective_account_profile,
    get_portal_state,
    persist_portal_state,
    update_refund_workflow,
)
from services.demo_users import DEMO_USERS, account_status_label
from services.portal_display import (
    booking_detail_markdown,
    booking_for_refund_display,
    refund_reason_label,
    ticket_why_raised_markdown,
)
from services.refund_eligibility import advance_demo_workflow
from services.refund_policy_config import REFUND_WORKFLOW_STATUSES
from services.ui_components import section_heading
from services.ui_copy import polish_ui_copy

_REFUND_TERMINAL = {"Rejected", "Completed (demo)", "Completed"}
_TICKET_CLOSED = {"resolved", "closed", "approved"}


def inject_admin_console_styles() -> None:
    st.markdown(
        """
        <style>
        .admin-attention {
            border-left: 4px solid #f59e0b;
            padding: 0.5rem 0.75rem;
            margin: 0.35rem 0;
            background: #fffbeb;
            border-radius: 0 8px 8px 0;
            font-size: 0.9rem;
        }
        [data-testid="stTabs"] [data-baseweb="tab-list"] {
            gap: 0.35rem;
            flex-wrap: wrap;
        }
        [data-testid="stTabs"] [data-baseweb="tab"] {
            font-size: 0.8rem !important;
            padding: 0.35rem 0.65rem !important;
            min-height: 2rem;
        }
        [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {
            background: #f0fdfa !important;
            border-radius: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _user_name(uid: str) -> str:
    return DEMO_USERS.get(uid, {}).get("display_name", uid)


def get_admin_queue_counts(state: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
    return _queue_counts(state or get_portal_state())


def _queue_counts(state: Dict[str, Any]) -> Dict[str, int]:
    refunds = state.get("refund_requests") or []
    tickets = state.get("support_tickets") or []
    appeals = state.get("account_appeals") or []
    pending_refunds = [
        r for r in refunds if r.get("workflow_status") not in _REFUND_TERMINAL
    ]
    open_tickets = [
        t
        for t in tickets
        if (t.get("status") or "").lower() not in _TICKET_CLOSED
    ]
    open_appeals = [
        a for a in appeals if (a.get("status") or "").lower() in ("submitted", "under review")
    ]
    restricted = sum(
        1
        for u in DEMO_USERS.values()
        if effective_account_profile(u["user_id"]).get("account_status") != "active"
    )
    return {
        "pending_refunds": len(pending_refunds),
        "open_tickets": len(open_tickets),
        "open_appeals": len(open_appeals),
        "restricted": restricted,
        "total_refunds": len(refunds),
        "total_tickets": len(tickets),
    }


def render_admin_unlock_gate() -> bool:
    if st.session_state.get("admin_unlocked"):
        return True
    st.info(
        "Switch to **🔧 Admin** at the top of the sidebar, or enter the admin passphrase below."
    )
    if st.text_input("Admin passphrase", type="password", key="admin_pass_gate") == "demo_admin":
        st.session_state.admin_unlocked = True
        st.rerun()
    st.caption("Admin passphrase is configured for your environment.")
    return False


def _tab_labels(counts: Dict[str, int]) -> List[str]:
    refunds = (
        f"Refunds ({counts['pending_refunds']})"
        if counts["pending_refunds"]
        else "Refunds"
    )
    tickets = (
        f"Tickets ({counts['open_tickets']})" if counts["open_tickets"] else "Tickets"
    )
    accounts = (
        f"Accounts ({counts['open_appeals']})"
        if counts["open_appeals"]
        else "Accounts"
    )
    return ["Overview", refunds, tickets, accounts, "Audit log"]


def render_admin_console(show_warning: bool = True) -> None:
    inject_admin_console_styles()
    state = get_portal_state()
    counts = _queue_counts(state)

    st.markdown("### 🔧 Admin console")
    if show_warning:
        st.caption("Prototype back-office — actions update local portal state immediately.")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Refunds to process", counts["pending_refunds"])
    m2.metric("Open tickets", counts["open_tickets"])
    m3.metric("Appeals waiting", counts["open_appeals"])
    m4.metric("Restricted users", counts["restricted"])

    tabs = st.tabs(_tab_labels(counts))
    with tabs[0]:
        _render_overview(state, counts)
    with tabs[1]:
        _render_refunds(state)
    with tabs[2]:
        _render_tickets(state, embedded=False)
    with tabs[3]:
        _render_accounts(state)
    with tabs[4]:
        _render_audit(state)


def _render_overview(state: Dict[str, Any], counts: Dict[str, int]) -> None:
    st.markdown("**Start here** — use the tabs above to jump between queues.")

    section_heading("Needs attention", variant="travel-sub")
    attention = 0
    for r in state.get("refund_requests") or []:
        if r.get("workflow_status") in _REFUND_TERMINAL:
            continue
        attention += 1
        st.markdown(
            f'<div class="admin-attention">🧾 Refund <strong>{r.get("request_id")}</strong> · '
            f'{_user_name(r.get("user_id", ""))} · <strong>{polish_ui_copy(str(r.get("workflow_status", "")))}</strong></div>',
            unsafe_allow_html=True,
        )
    for t in state.get("support_tickets") or []:
        if (t.get("status") or "").lower() in _TICKET_CLOSED:
            continue
        attention += 1
        st.markdown(
            f'<div class="admin-attention">💬 Ticket <strong>{t.get("ticket_id")}</strong> · '
            f'{_user_name(t.get("user_id", ""))} · <strong>{t.get("status")}</strong> — '
            f'{t.get("subject", "")[:60]}</div>',
            unsafe_allow_html=True,
        )
    for a in state.get("account_appeals") or []:
        if (a.get("status") or "").lower() not in ("submitted", "under review"):
            continue
        attention += 1
        st.markdown(
            f'<div class="admin-attention">🛡️ Appeal <strong>{a.get("appeal_id")}</strong> · '
            f'{_user_name(a.get("user_id", ""))}</div>',
            unsafe_allow_html=True,
        )
    if attention == 0:
        st.success("All queues are clear for this snapshot.")

    try:
        import app as trip_app

        st.markdown("**Related pages**")
        l1, l2, l3 = st.columns(3)
        l1.page_link(trip_app.BOOKINGS_PAGE, label="Bookings reference", icon="🧳")
        l2.page_link(trip_app.SUPPORT_PAGE, label="Support (customer UI)", icon="💬")
        l3.page_link(trip_app.ACCOUNT_PAGE, label="Account status", icon="🛡️")
    except Exception:
        pass


def _render_refunds(state: Dict[str, Any]) -> None:
    refunds: List[dict] = list(state.get("refund_requests") or [])
    section_heading("Refund requests", variant="travel")

    filter_mode = st.radio(
        "Show",
        ["Needs action", "All", "Completed / rejected"],
        horizontal=True,
        key="admin_refund_filter",
    )
    search = st.text_input("Search by ID, user, or booking", key="admin_refund_search").strip().lower()

    def _matches(r: dict) -> bool:
        status = r.get("workflow_status", "")
        if filter_mode == "Needs action" and status in _REFUND_TERMINAL:
            return False
        if filter_mode == "Completed / rejected" and status not in _REFUND_TERMINAL:
            return False
        if search:
            blob = " ".join(
                [
                    str(r.get("request_id", "")),
                    str(r.get("user_id", "")),
                    str(r.get("booking_id", "")),
                    _user_name(r.get("user_id", "")).lower(),
                ]
            ).lower()
            if search not in blob:
                return False
        return True

    filtered = [r for r in reversed(refunds) if _matches(r)]
    if not filtered:
        st.info("No refund requests match this filter.")
        return

    flow = polish_ui_copy(" → ".join(REFUND_WORKFLOW_STATUSES))
    st.caption(f"Showing **{len(filtered)}** request(s). Workflow: {flow}")

    for r in filtered:
        rid = r.get("request_id", "")
        uid = r.get("user_id", "")
        status = r.get("workflow_status", "Submitted")
        nxt = advance_demo_workflow(status)
        title = polish_ui_copy(
            f"{rid} · {_user_name(uid)} · {r.get('booking_id')} · **{status}**"
        )
        with st.expander(title, expanded=status not in _REFUND_TERMINAL):
            st.markdown(f"**Customer:** `{uid}` ({_user_name(uid)})")
            st.markdown(
                f"**Why the customer raised this:** "
                f"{refund_reason_label(str(r.get('reason', '')))}"
            )
            st.markdown(f"**Eligibility:** {r.get('eligibility', '—')}")
            expl = r.get("explanation_detail") or r.get("explanation", "")
            if expl:
                st.info(expl)
            booking = booking_for_refund_display(str(r.get("booking_id", "")))
            if booking:
                st.markdown("**Booking / ticket under review**")
                st.markdown(booking_detail_markdown(booking))
            else:
                st.caption(f"No booking record for `{r.get('booking_id')}` in sample data.")
            if r.get("status_history"):
                with st.popover("Status history"):
                    for h in r["status_history"][-8:]:
                        st.caption(f"{h.get('ts', '')[:16]} · **{h.get('status')}** — {h.get('note', '')}")

            note = st.text_input("Admin note (optional)", key=f"ref_note_{rid}")
            c1, c2, c3, c4 = st.columns(4)
            if c1.button(
                f"Next: {polish_ui_copy(nxt)}" if nxt else "At final step",
                key=f"ref_adv_{rid}",
                disabled=not nxt,
                type="primary",
            ):
                update_refund_workflow(rid, nxt, note=note or "Admin advance")
                st.toast(f"Refund {rid} → {nxt}")
                st.rerun()
            if c2.button("Approve now", key=f"ref_appr_{rid}"):
                update_refund_workflow(rid, "Approved", note=note or "Admin approval")
                st.toast(f"Refund {rid} approved")
                st.rerun()
            if c3.button("Reject", key=f"ref_rej_{rid}"):
                update_refund_workflow(rid, "Rejected", note=note or "Admin rejection")
                st.toast(f"Refund {rid} rejected")
                st.rerun()
            if c4.button("Mark completed", key=f"ref_done_{rid}"):
                update_refund_workflow(
                    rid, "Completed (demo)", note=note or "Payout completed"
                )
                st.toast(f"Refund {rid} completed")
                st.rerun()


def _render_ticket_card(t: dict, *, compact: bool) -> None:
    tid = t.get("ticket_id", "")
    uid = t.get("user_id", "")
    name = _user_name(uid)
    status = t.get("status") or "Open"
    closed = (status or "").lower() in _TICKET_CLOSED
    title = f"{tid} · {name} · {status} — {t.get('subject', '')[:50]}"

    with st.expander(title, expanded=not closed and not compact):
        st.markdown("**Why this ticket was raised**")
        st.markdown(ticket_why_raised_markdown(t))
        st.divider()
        st.markdown("**Conversation**")
        for msg in t.get("messages") or []:
            who = "Customer" if msg.get("from") == "user" else "Support"
            st.markdown(f"**{who}:** {polish_ui_copy(msg.get('body', ''))}")

        try:
            idx = ADMIN_TICKET_STATUSES.index(status)
        except ValueError:
            idx = 0
        new_status = st.selectbox(
            "Status",
            ADMIN_TICKET_STATUSES,
            index=idx,
            key=f"adm_tk_status_{tid}",
        )
        note = st.text_input(
            "Reply to customer (optional)",
            key=f"adm_tk_note_{tid}",
            placeholder="Customer sees this on their ticket thread.",
        )
        c1, c2, c3 = st.columns(3)
        if c1.button("Save", key=f"adm_tk_save_{tid}", type="primary"):
            admin_update_ticket(tid, new_status, note or None)
            st.toast(f"Ticket {tid} → {new_status}")
            st.rerun()
        if c2.button("Approve", key=f"adm_tk_approve_{tid}"):
            body = note.strip() if note and note.strip() else (
                "Your request has been approved by support."
            )
            admin_update_ticket(tid, "Approved", body)
            st.toast(f"Ticket {tid} approved")
            st.rerun()
        if c3.button("Resolve", key=f"adm_tk_resolve_{tid}"):
            body = note.strip() if note and note.strip() else (
                "This ticket is resolved. Thank you for contacting support."
            )
            admin_update_ticket(tid, "Resolved", body)
            st.toast(f"Ticket {tid} resolved")
            st.rerun()


def _render_tickets(state: Dict[str, Any], *, embedded: bool) -> None:
    tickets: List[dict] = list(state.get("support_tickets") or [])
    if not embedded:
        section_heading("Support tickets", variant="travel")

    show = st.radio(
        "Show",
        ["Open only", "All tickets"],
        horizontal=True,
        key="admin_ticket_filter",
    )
    cat_filter = st.selectbox(
        "Category",
        ["All categories"]
        + sorted({t.get("category", "Other") for t in tickets}),
        key="admin_ticket_cat",
    )

    def _ok(t: dict) -> bool:
        st_lower = (t.get("status") or "").lower()
        if show == "Open only" and st_lower in _TICKET_CLOSED:
            return False
        if cat_filter != "All categories" and t.get("category") != cat_filter:
            return False
        return True

    filtered = [t for t in reversed(tickets) if _ok(t)]
    if not filtered:
        st.info("No tickets match this filter.")
        return

    st.caption(f"**{len(filtered)}** ticket(s) — use **Approve** or **Resolve** for one-click actions.")
    for t in filtered[:50 if not embedded else 10]:
        _render_ticket_card(t, compact=embedded)


def render_admin_tickets_embedded(limit: int = 10, heading: str = "Support tickets") -> None:
    """Compact ticket tools for Support page admin strip."""
    section_heading(heading, variant="travel")
    state = get_portal_state()
    tickets = state.get("support_tickets") or []
    if not tickets:
        st.caption("No tickets in portal state.")
        return
    st.caption("Open tickets are expanded first. Full queue: **Admin console → Tickets**.")
    for t in reversed(tickets[-limit:]):
        _render_ticket_card(t, compact=True)


def _render_accounts(state: Dict[str, Any]) -> None:
    section_heading("Customer accounts", variant="travel")
    st.caption("Tap a user to review status and apply overrides.")

    uid = st.selectbox(
        "Select customer",
        options=list(DEMO_USERS.keys()),
        format_func=lambda x: f"{DEMO_USERS[x]['display_name']} ({account_status_label(effective_account_profile(x).get('account_status', 'active'))})",
        key="admin_acct_user",
    )
    profile = effective_account_profile(uid)
    st.markdown(
        f"**Current status:** {account_status_label(profile.get('account_status', 'active'))}"
    )
    for n in profile.get("restriction_notes") or []:
        st.caption(f"· {n.get('summary', '')}")

    new_status = st.selectbox(
        "Set new status",
        ["active", "under_review", "temporarily_restricted", "blacklisted"],
        format_func=account_status_label,
        key="admin_acct_new_status",
    )
    reason = st.text_input("Reason (saved to audit log)", key="admin_acct_reason")
    if st.button("Apply status", type="primary", key="admin_acct_apply"):
        admin_set_account_status(uid, new_status, reason or "Admin update")
        st.success(f"Updated **{_user_name(uid)}** → {account_status_label(new_status)}")
        st.rerun()

    section_heading("Appeals queue", variant="travel-sub")
    appeals = state.get("account_appeals") or []
    if not appeals:
        st.caption("No appeals.")
        return
    for a in reversed(appeals):
        aid = a.get("appeal_id", "")
        auid = a.get("user_id", "")
        with st.container(border=True):
            st.markdown(
                f"**{aid}** · {_user_name(auid)} · **{a.get('status', 'Submitted')}**"
            )
            st.write(a.get("message", ""))
            anote = st.text_input("Decision note", key=f"appeal_note_{aid}")
            c1, c2 = st.columns(2)
            if c1.button("Approve appeal", key=f"appeal_ok_{aid}", type="primary"):
                _resolve_appeal(aid, "Approved", anote, restore_active=True)
                st.toast(f"Appeal {aid} approved")
                st.rerun()
            if c2.button("Deny appeal", key=f"appeal_no_{aid}"):
                _resolve_appeal(aid, "Denied", anote, restore_active=False)
                st.toast(f"Appeal {aid} denied")
                st.rerun()


def _resolve_appeal(
    appeal_id: str, status: str, note: str, *, restore_active: bool
) -> None:
    state = get_portal_state()
    for a in state.get("account_appeals", []):
        if a.get("appeal_id") != appeal_id:
            continue
        a["status"] = status
        if note:
            a["admin_note"] = note
        uid = a.get("user_id", "")
        append_audit(
            state,
            "appeal_decision",
            f"{status}: {note or ''}",
            user_id=uid,
            ref=appeal_id,
        )
        persist_portal_state()
        if restore_active and uid:
            admin_set_account_status(uid, "active", note or "Appeal approved")
        return


def _render_audit(state: Dict[str, Any]) -> None:
    section_heading("Audit log", variant="travel")
    log = list(state.get("audit_log") or [])
    actions = sorted({row.get("action", "") for row in log if row.get("action")})
    action_pick = st.selectbox("Filter by action", ["All"] + actions, key="admin_audit_action")
    search = st.text_input("Search detail or ref", key="admin_audit_search").strip().lower()

    rows = reversed(log)
    shown = 0
    for row in rows:
        if action_pick != "All" and row.get("action") != action_pick:
            continue
        detail = str(row.get("detail", ""))
        ref = str(row.get("ref", ""))
        if search and search not in (detail + ref).lower():
            continue
        shown += 1
        if shown > 40:
            break
        st.markdown(
            f"`{row.get('ts', '')[:19]}` · **{row.get('action')}** · "
            f"{detail[:100]}"
            + (f" · ref `{ref}`" if ref else "")
            + (f" · user `{row.get('user_id')}`" if row.get("user_id") else "")
        )
    if shown == 0:
        st.caption("No audit entries match.")
