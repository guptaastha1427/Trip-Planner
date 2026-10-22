"""
Persistence for demo refunds, support tickets, appeals, and audit log.

Stored in data/customer_portal_state.json (gitignored at runtime).
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import streamlit as st

from config import CUSTOMER_PORTAL_STATE_PATH, DATA_DIR
from services.demo_users import DEFAULT_USER_ID, DEMO_USERS, get_demo_user


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _empty_state() -> Dict[str, Any]:
    return {
        "current_user_id": DEFAULT_USER_ID,
        "refund_requests": [],
        "support_tickets": [],
        "account_appeals": [],
        "audit_log": [],
        "account_overrides": {},
        "user_bookings": [],
        "seeded": False,
    }


def load_portal_state() -> Dict[str, Any]:
    ensure_data_dir()
    if not CUSTOMER_PORTAL_STATE_PATH.is_file():
        return _empty_state()
    try:
        data = json.loads(CUSTOMER_PORTAL_STATE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return _empty_state()
    for key in _empty_state():
        data.setdefault(key, _empty_state()[key])
    return data


def save_portal_state(state: Dict[str, Any]) -> None:
    ensure_data_dir()
    CUSTOMER_PORTAL_STATE_PATH.write_text(
        json.dumps(state, indent=2), encoding="utf-8"
    )


def append_audit(
    state: Dict[str, Any],
    action: str,
    detail: str,
    user_id: Optional[str] = None,
    ref: Optional[str] = None,
) -> None:
    state.setdefault("audit_log", []).append(
        {
            "ts": _utc_now_iso(),
            "action": action,
            "detail": detail,
            "user_id": user_id,
            "ref": ref,
        }
    )


def bootstrap_demo_data(state: Dict[str, Any]) -> Dict[str, Any]:
    """One-time seed: duplicate refund on Sam's flight, open support ticket for dispute."""
    if state.get("seeded"):
        return state
    state["seeded"] = True
    # Scenario 6: duplicate refund request already exists for BK-FLT-1201
    state["refund_requests"].append(
        {
            "request_id": "RR-DEMO-0001",
            "user_id": "user_sam",
            "booking_id": "BK-FLT-1201",
            "reason": "change_plans",
            "eligibility": "Not Eligible",
            "workflow_status": "Rejected",
            "original_amount": 9100.0,
            "cancellation_fee": 9100.0,
            "estimated_refund": 0.0,
            "currency": "INR",
            "explanation": "Booking already refunded (demo).",
            "status_history": [
                {"ts": "2026-09-10T10:00:00+00:00", "status": "Submitted"},
                {"ts": "2026-09-10T10:00:05+00:00", "status": "Rejected"},
            ],
            "created_at": "2026-09-10T10:00:00+00:00",
        }
    )
    state["support_tickets"].append(
        {
            "ticket_id": "TK-DEMO-0001",
            "user_id": "user_maya",
            "category": "Refund Issue",
            "subject": "Dispute partial refund on saver fare",
            "status": "In Progress",
            "created_at": "2026-10-05T09:00:00+00:00",
            "messages": [
                {
                    "ts": "2026-10-05T09:00:00+00:00",
                    "from": "user",
                    "body": "I expected a higher refund on BK-FLT-1101. Please review.",
                },
                {
                    "ts": "2026-10-05T11:30:00+00:00",
                    "from": "support",
                    "body": "We applied the saver fare policy (demo). Escalation noted.",
                },
            ],
        }
    )
    state["account_appeals"].append(
        {
            "appeal_id": "AP-DEMO-0001",
            "user_id": "user_restricted",
            "status": "Under Review",
            "message": "I believe the duplicate claim was a mistake. Please review my restriction.",
            "created_at": "2026-10-10T08:00:00+00:00",
        }
    )
    append_audit(
        state,
        "bootstrap",
        "Loaded demo refund, ticket, and appeal samples",
    )
    return state


def init_portal_session() -> None:
    if st.session_state.get("portal_bootstrapped"):
        return
    disk = bootstrap_demo_data(load_portal_state())
    save_portal_state(disk)
    st.session_state.portal_bootstrapped = True
    st.session_state.portal_state = disk
    st.session_state.demo_user_id = disk.get("current_user_id", DEFAULT_USER_ID)


def get_portal_state() -> Dict[str, Any]:
    init_portal_session()
    if "portal_state" not in st.session_state:
        st.session_state.portal_state = bootstrap_demo_data(load_portal_state())
    state = st.session_state.portal_state
    for key, default in _empty_state().items():
        state.setdefault(key, default if not isinstance(default, list) else [])
    return state


def persist_portal_state() -> None:
    state = get_portal_state()
    state["current_user_id"] = st.session_state.get(
        "demo_user_id", state.get("current_user_id", DEFAULT_USER_ID)
    )
    save_portal_state(state)


def set_demo_user(user_id: str) -> None:
    st.session_state.demo_user_id = user_id
    state = get_portal_state()
    state["current_user_id"] = user_id
    persist_portal_state()


def effective_account_profile(user_id: str) -> Dict[str, Any]:
    base = dict(get_demo_user(user_id))
    overrides = get_portal_state().get("account_overrides", {}).get(user_id, {})
    if overrides:
        base.update(overrides)
    return base


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def add_user_booking(record: Dict[str, Any]) -> Dict[str, Any]:
    """Persist a demo package booking for the current portal user."""
    state = get_portal_state()
    state.setdefault("user_bookings", []).append(record)
    append_audit(
        state,
        "booking_created",
        f"{record.get('package_name', 'Package')} · {record.get('origin')} → {record.get('destination')}",
        user_id=record.get("user_id"),
        ref=record.get("booking_id"),
    )
    persist_portal_state()
    return record


def list_user_bookings() -> List[Dict[str, Any]]:
    return list(get_portal_state().get("user_bookings") or [])


def list_refunds_for_user(user_id: str) -> List[Dict[str, Any]]:
    return [
        r
        for r in get_portal_state().get("refund_requests", [])
        if r.get("user_id") == user_id
    ]


def get_refund_request(request_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    for r in get_portal_state().get("refund_requests", []):
        if r.get("request_id") == request_id and r.get("user_id") == user_id:
            return r
    return None


def find_refund_for_booking(user_id: str, booking_id: str) -> Optional[Dict[str, Any]]:
    for r in get_portal_state().get("refund_requests", []):
        if r.get("user_id") == user_id and r.get("booking_id") == booking_id:
            return r
    return None


def add_refund_request(record: Dict[str, Any]) -> Dict[str, Any]:
    state = get_portal_state()
    state.setdefault("refund_requests", []).append(record)
    append_audit(
        state,
        "refund_created",
        record.get("explanation", ""),
        user_id=record.get("user_id"),
        ref=record.get("request_id"),
    )
    persist_portal_state()
    return record


def update_refund_workflow(
    request_id: str,
    new_status: str,
    note: Optional[str] = None,
    admin: bool = False,
) -> bool:
    state = get_portal_state()
    for r in state.get("refund_requests", []):
        if r.get("request_id") != request_id:
            continue
        r.setdefault("status_history", []).append(
            {"ts": _utc_now_iso(), "status": new_status, "note": note or ""}
        )
        r["workflow_status"] = new_status
        append_audit(
            state,
            "refund_status",
            f"{new_status}: {note or ''}",
            user_id=r.get("user_id"),
            ref=request_id,
        )
        persist_portal_state()
        return True
    return False


def list_tickets_for_user(user_id: str) -> List[Dict[str, Any]]:
    return [
        t
        for t in get_portal_state().get("support_tickets", [])
        if t.get("user_id") == user_id
    ]


def get_ticket(ticket_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    for t in get_portal_state().get("support_tickets", []):
        if t.get("ticket_id") == ticket_id and t.get("user_id") == user_id:
            return t
    return None


def get_ticket_by_id(ticket_id: str) -> Optional[Dict[str, Any]]:
    for t in get_portal_state().get("support_tickets", []):
        if t.get("ticket_id") == ticket_id:
            return t
    return None


ADMIN_TICKET_STATUSES = [
    "Open",
    "In Progress",
    "Awaiting User Response",
    "Approved",
    "Resolved",
    "Closed",
]


def create_support_ticket(
    user_id: str,
    category: str,
    subject: str,
    body: str,
) -> Dict[str, Any]:
    state = get_portal_state()
    ticket = {
        "ticket_id": new_id("TK"),
        "user_id": user_id,
        "category": category,
        "subject": subject,
        "status": "Open",
        "created_at": _utc_now_iso(),
        "messages": [{"ts": _utc_now_iso(), "from": "user", "body": body}],
    }
    state.setdefault("support_tickets", []).append(ticket)
    append_audit(state, "ticket_created", subject, user_id=user_id, ref=ticket["ticket_id"])
    persist_portal_state()
    return ticket


def set_ticket_status(ticket_id: str, user_id: str, status: str) -> bool:
    state = get_portal_state()
    for t in state.get("support_tickets", []):
        if t.get("ticket_id") == ticket_id and t.get("user_id") == user_id:
            t["status"] = status
            append_audit(
                state,
                "ticket_status",
                status,
                user_id=user_id,
                ref=ticket_id,
            )
            persist_portal_state()
            return True
    return False


def admin_update_ticket(
    ticket_id: str,
    status: str,
    admin_note: Optional[str] = None,
) -> bool:
    """Back-office only: set status and optional support reply on any ticket."""
    state = get_portal_state()
    for t in state.get("support_tickets", []):
        if t.get("ticket_id") != ticket_id:
            continue
        t["status"] = status
        if admin_note and admin_note.strip():
            t.setdefault("messages", []).append(
                {
                    "ts": _utc_now_iso(),
                    "from": "support",
                    "body": admin_note.strip(),
                }
            )
        append_audit(
            state,
            "ticket_admin_update",
            f"{status}: {(admin_note or '')[:120]}",
            user_id=t.get("user_id"),
            ref=ticket_id,
        )
        persist_portal_state()
        return True
    return False


def add_ticket_message(
    ticket_id: str,
    user_id: str,
    body: str,
    from_role: str = "user",
) -> bool:
    state = get_portal_state()
    for t in state.get("support_tickets", []):
        if t.get("ticket_id") == ticket_id and t.get("user_id") == user_id:
            t.setdefault("messages", []).append(
                {"ts": _utc_now_iso(), "from": from_role, "body": body}
            )
            if from_role == "user" and t.get("status") == "Awaiting User Response":
                t["status"] = "In Progress"
            persist_portal_state()
            return True
    return False


def submit_appeal(user_id: str, message: str) -> Dict[str, Any]:
    state = get_portal_state()
    appeal = {
        "appeal_id": new_id("AP"),
        "user_id": user_id,
        "status": "Submitted",
        "message": message,
        "created_at": _utc_now_iso(),
    }
    state.setdefault("account_appeals", []).append(appeal)
    append_audit(state, "appeal_submitted", message[:120], user_id=user_id, ref=appeal["appeal_id"])
    persist_portal_state()
    return appeal


def admin_set_account_status(
    user_id: str,
    account_status: str,
    reason: str,
) -> None:
    if user_id not in DEMO_USERS:
        return
    state = get_portal_state()
    state.setdefault("account_overrides", {})[user_id] = {
        "account_status": account_status,
        "restriction_notes": [
            {
                "code": "admin_action",
                "summary": reason,
                "date": _utc_now_iso()[:10],
                "booking_ref": "",
            }
        ],
    }
    append_audit(
        state,
        "account_status_change",
        f"{user_id} -> {account_status}: {reason}",
        user_id=user_id,
    )
    persist_portal_state()
