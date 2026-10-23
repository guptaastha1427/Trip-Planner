"""Resolve which customer portal profile is active (auth, admin preview, or guest)."""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional

import streamlit as st

from services.customer_portal_store import get_portal_state, get_registered_customers, set_demo_user
from services.demo_dashboard import is_admin_dashboard_mode
from services.demo_users import ACCOUNT_ACTIVE, DEFAULT_USER_ID, DEMO_USERS, get_demo_user
from services.rag_chat_auth import current_user, is_logged_in


def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def demo_user_id_for_email(email: str) -> Optional[str]:
    """Map a login email to a seeded demo customer when addresses match."""
    em = _normalize_email(email)
    if not em:
        return None
    for uid, profile in DEMO_USERS.items():
        if _normalize_email(str(profile.get("email", ""))) == em:
            return uid
    return None


def portal_user_id_for_email(email: str) -> str:
    """Stable portal user id for an email (demo seed or registered auth id)."""
    mapped = demo_user_id_for_email(email)
    if mapped:
        return mapped
    em = _normalize_email(email)
    if not em:
        return DEFAULT_USER_ID
    digest = hashlib.sha256(em.encode("utf-8")).hexdigest()[:16]
    return f"auth_{digest}"


def portal_user_id_for_auth() -> str:
    """Stable portal user id for the logged-in app account."""
    auth = current_user() or {}
    return portal_user_id_for_email(str(auth.get("email", "")))


def list_portal_customer_ids() -> List[str]:
    """Demo seed accounts plus persisted registered signups (order stable for UI)."""
    demo_ids = list(DEMO_USERS.keys())
    reg = get_registered_customers()
    reg_ids = sorted(uid for uid in reg if uid not in DEMO_USERS)
    return demo_ids + reg_ids


def is_known_portal_customer(user_id: str) -> bool:
    return user_id in DEMO_USERS or user_id in get_registered_customers()


def portal_customer_label(user_id: str) -> str:
    if user_id in DEMO_USERS:
        return str(DEMO_USERS[user_id].get("display_name") or user_id)
    reg = get_registered_customers().get(user_id)
    if reg:
        return str(reg.get("display_name") or reg.get("username") or user_id)
    return user_id


def can_pick_customer_preview() -> bool:
    """Only admins (dashboard mode) may switch the customer preview account."""
    return is_admin_dashboard_mode()


def portal_user_display_name(user_id: str) -> str:
    profile = effective_portal_profile(user_id)
    return str(profile.get("display_name") or user_id)


def effective_portal_profile(user_id: str) -> Dict[str, Any]:
    """Account row for UI — demo seed, auth-only user, or overrides."""
    if user_id in DEMO_USERS:
        base = dict(get_demo_user(user_id))
        overrides = get_portal_state().get("account_overrides", {}).get(user_id, {})
        if overrides:
            base.update(overrides)
        return base

    reg = get_registered_customers().get(user_id)
    if reg:
        profile = dict(reg)
        overrides = get_portal_state().get("account_overrides", {}).get(user_id, {})
        if overrides:
            profile.update(overrides)
        return profile

    if user_id.startswith("auth_") and is_logged_in():
        auth = current_user() or {}
        if portal_user_id_for_auth() == user_id:
            return {
                "user_id": user_id,
                "display_name": auth.get("username") or auth.get("email") or "User",
                "email": auth.get("email", ""),
                "account_status": ACCOUNT_ACTIVE,
                "restriction_notes": [],
            }

    return dict(get_demo_user(user_id))


def _sync_admin_customer_selection() -> str:
    state = get_portal_state()
    current = st.session_state.get("demo_user_id") or state.get(
        "current_user_id", DEFAULT_USER_ID
    )
    options = list_portal_customer_ids()
    if current not in options:
        current = options[0]
    if "portal_demo_user_select" not in st.session_state:
        st.session_state.portal_demo_user_select = current
    choice = st.session_state.portal_demo_user_select
    if choice not in options:
        choice = current
        st.session_state.portal_demo_user_select = choice
    if st.session_state.get("demo_user_id") != choice:
        set_demo_user(choice)
    return choice


def _sync_guest_demo_selection() -> str:
    state = get_portal_state()
    current = st.session_state.get("demo_user_id") or state.get(
        "current_user_id", DEFAULT_USER_ID
    )
    options = list_portal_customer_ids()
    if current not in options:
        current = options[0]
    if "portal_demo_user_select" not in st.session_state:
        st.session_state.portal_demo_user_select = current
    choice = st.session_state.portal_demo_user_select
    if choice not in options:
        choice = current
        st.session_state.portal_demo_user_select = choice
    if st.session_state.get("demo_user_id") != choice:
        set_demo_user(choice)
    return choice


def _bind_logged_in_portal_user() -> str:
    uid = portal_user_id_for_auth()
    st.session_state.demo_user_id = uid
    st.session_state.portal_demo_user_select = uid
    return uid


def sync_portal_user_context() -> str:
    """
    Keep ``demo_user_id`` aligned with session rules:
    - Admin mode → sidebar customer preview selection
    - Logged-in user mode → that user's portal id (email map or auth_* id)
    - Guest → guest preview selection
    """
    get_portal_state()
    if can_pick_customer_preview():
        uid = _sync_admin_customer_selection()
    elif is_logged_in():
        uid = _bind_logged_in_portal_user()
    else:
        uid = _sync_guest_demo_selection()
    st.session_state.demo_user_id = uid
    return uid


def resolve_portal_user_id() -> str:
    """Active portal user id for data filtering (bookings, refunds, trips, RAG context)."""
    uid = st.session_state.get("demo_user_id")
    if isinstance(uid, str) and uid:
        if can_pick_customer_preview():
            return uid if is_known_portal_customer(uid) else _sync_admin_customer_selection()
        if is_logged_in():
            expected = portal_user_id_for_auth()
            if uid != expected:
                return _bind_logged_in_portal_user()
            return expected
        if is_known_portal_customer(uid):
            return uid
    return sync_portal_user_context()
