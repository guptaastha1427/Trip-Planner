"""
Signup / login for the Document & Policy Assistant.

Accounts live in ``data/rag_chat_users.json`` (passwords hashed with PBKDF2).
Active sessions are stored server-side in ``data/rag_chat_sessions.json`` and
referenced from the browser via an HTTP-only-style session cookie (demo).
"""

from __future__ import annotations

import hashlib
import json
import re
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st

from config import DATA_DIR

USERS_PATH = DATA_DIR / "rag_chat_users.json"
SESSIONS_PATH = DATA_DIR / "rag_chat_sessions.json"
SESSION_USER_KEY = "rag_chat_user"
SESSION_TOKEN_KEY = "rag_auth_token"
_AUTH_COOKIE = "trip_planner_auth"
_COOKIE_MANAGER_KEY = "rag_auth_cookie_manager"

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PBKDF2_ITERATIONS = 260_000
_MIN_PASSWORD_LEN = 8


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _public_profile(user: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "username": user.get("username", ""),
        "email": user.get("email", ""),
        "created_at": user.get("created_at", ""),
    }


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        _PBKDF2_ITERATIONS,
    )
    return f"pbkdf2_sha256${_PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        algo, iterations_s, salt_hex, digest_hex = stored.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        iterations = int(iterations_s)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
    except (ValueError, TypeError):
        return False
    actual = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return secrets.compare_digest(actual, expected)


def list_auth_user_profiles() -> List[Dict[str, Any]]:
    """Public profiles for all Document Assistant accounts (no password hashes)."""
    return [_public_profile(u) for u in _load_users()]


def _load_users() -> List[Dict[str, Any]]:
    if not USERS_PATH.is_file():
        return []
    try:
        data = json.loads(USERS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("users"), list):
        return data["users"]
    return []


def _save_users(users: List[Dict[str, Any]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    USERS_PATH.write_text(
        json.dumps({"users": users}, indent=2),
        encoding="utf-8",
    )


def _load_sessions() -> Dict[str, Dict[str, Any]]:
    if not SESSIONS_PATH.is_file():
        return {}
    try:
        data = json.loads(SESSIONS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    if isinstance(data, dict) and isinstance(data.get("sessions"), dict):
        return data["sessions"]
    return {}


def _save_sessions(sessions: Dict[str, Dict[str, Any]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SESSIONS_PATH.write_text(
        json.dumps({"sessions": sessions}, indent=2),
        encoding="utf-8",
    )


def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def _normalize_username(username: str) -> str:
    return (username or "").strip()


def _find_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    em = _normalize_email(email)
    for u in _load_users():
        if _normalize_email(u.get("email", "")) == em:
            return u
    return None


def _cookie_manager():
    try:
        from extra_streamlit_components import CookieManager
    except ImportError:
        return None
    if _COOKIE_MANAGER_KEY not in st.session_state:
        st.session_state[_COOKIE_MANAGER_KEY] = CookieManager()
    return st.session_state[_COOKIE_MANAGER_KEY]


def _read_auth_cookie() -> Optional[str]:
    cm = _cookie_manager()
    if cm is None:
        return None
    try:
        token = cm.get(_AUTH_COOKIE)
    except Exception:
        return None
    if token and isinstance(token, str) and token.strip():
        return token.strip()
    return None


def _write_auth_cookie(token: str) -> None:
    cm = _cookie_manager()
    if cm is None:
        return
    expires = datetime.now() + timedelta(days=30)
    try:
        cm.set(
            _AUTH_COOKIE,
            token,
            expires_at=expires,
            key=f"rag_set_cookie_{token[:8]}",
        )
    except Exception:
        pass


def _clear_auth_cookie() -> None:
    cm = _cookie_manager()
    if cm is None:
        return
    try:
        cm.delete(_AUTH_COOKIE, key="rag_delete_auth_cookie")
    except Exception:
        pass


def _read_portal_persisted_token() -> Optional[str]:
    try:
        from services.customer_portal_store import load_portal_state

        raw = load_portal_state().get("rag_session_token")
    except Exception:
        return None
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return None


def _persist_portal_auth_token(token: Optional[str]) -> None:
    try:
        from services.customer_portal_store import get_portal_state, save_portal_state

        state = get_portal_state()
        if token:
            state["rag_session_token"] = token
        else:
            state.pop("rag_session_token", None)
        save_portal_state(state)
    except Exception:
        pass


def mount_rag_auth_cookie_component() -> None:
    """Mount the cookie component early in the run (before other widgets)."""
    _cookie_manager()


def _create_server_session(email: str) -> str:
    token = secrets.token_urlsafe(32)
    sessions = _load_sessions()
    sessions[token] = {
        "email": _normalize_email(email),
        "created_at": _utc_now(),
    }
    _save_sessions(sessions)
    st.session_state[SESSION_TOKEN_KEY] = token
    _write_auth_cookie(token)
    _persist_portal_auth_token(token)
    return token


def _destroy_server_session(token: Optional[str]) -> None:
    if not token:
        return
    sessions = _load_sessions()
    if token in sessions:
        del sessions[token]
        _save_sessions(sessions)


def _apply_session_token(token: str) -> bool:
    sessions = _load_sessions()
    rec = sessions.get(token)
    if not rec:
        return False
    user = _find_user_by_email(str(rec.get("email", "")))
    if not user:
        return False
    st.session_state[SESSION_USER_KEY] = _public_profile(user)
    st.session_state[SESSION_TOKEN_KEY] = token
    return True


def init_rag_auth_session() -> None:
    """Restore logged-in user from session state, disk session, or auth cookie."""
    if current_user() is not None:
        return

    token = st.session_state.get(SESSION_TOKEN_KEY)
    if isinstance(token, str) and token and _apply_session_token(token):
        return

    portal_token = _read_portal_persisted_token()
    if portal_token and _apply_session_token(portal_token):
        return

    attempts = int(st.session_state.get("_rag_auth_cookie_attempts", 0))
    if attempts < 2:
        cookie_token = _read_auth_cookie()
        st.session_state["_rag_auth_cookie_attempts"] = attempts + 1
        if cookie_token and _apply_session_token(cookie_token):
            _persist_portal_auth_token(cookie_token)
            return
        if _cookie_manager() is not None and attempts == 0 and not cookie_token:
            st.rerun()


def _establish_login(user: Dict[str, Any]) -> None:
    st.session_state[SESSION_USER_KEY] = _public_profile(user)
    _create_server_session(str(user.get("email", "")))


def register_user(username: str, email: str, password: str) -> Tuple[bool, str]:
    name = _normalize_username(username)
    em = _normalize_email(email)
    pwd = password or ""
    if len(name) < 2:
        return False, "Username must be at least 2 characters."
    if not _EMAIL_RE.match(em):
        return False, "Please enter a valid email address."
    if len(pwd) < _MIN_PASSWORD_LEN:
        return False, f"Password must be at least {_MIN_PASSWORD_LEN} characters."

    users = _load_users()
    if any(_normalize_email(u.get("email", "")) == em for u in users):
        return False, "An account with this email already exists. Try signing in."
    if any(_normalize_username(u.get("username", "")).lower() == name.lower() for u in users):
        return False, "That username is already taken."

    profile = {
        "username": name,
        "email": em,
        "password_hash": _hash_password(pwd),
        "created_at": _utc_now(),
    }
    users.append(profile)
    _save_users(users)
    _establish_login(profile)
    from services.customer_portal_store import upsert_portal_customer

    upsert_portal_customer(name, em, created_at=str(profile.get("created_at", "")))
    return True, f"Welcome, {name}! Your account was created."


def login_user(email: str, password: str) -> Tuple[bool, str]:
    em = _normalize_email(email)
    pwd = password or ""
    if not _EMAIL_RE.match(em):
        return False, "Please enter a valid email address."
    if not pwd:
        return False, "Please enter your password."

    user = _find_user_by_email(em)
    if not user:
        return False, "No account found for that email. Create an account first."

    stored_hash = user.get("password_hash") or ""
    if not stored_hash:
        if len(pwd) < _MIN_PASSWORD_LEN:
            return (
                False,
                f"This account has no password yet. Use at least {_MIN_PASSWORD_LEN} "
                "characters to set one on first sign-in.",
            )
        user["password_hash"] = _hash_password(pwd)
        users = _load_users()
        for i, u in enumerate(users):
            if _normalize_email(u.get("email", "")) == em:
                users[i] = user
                break
        _save_users(users)

    elif not _verify_password(pwd, str(stored_hash)):
        return False, "Incorrect password. Try again or create a new account."

    _establish_login(user)
    from services.customer_portal_store import upsert_portal_customer

    upsert_portal_customer(
        str(user.get("username", em)),
        em,
        created_at=str(user.get("created_at", "")),
    )
    name = user.get("username", em)
    return True, f"Signed in as **{name}**."


def logout_user() -> None:
    token = st.session_state.get(SESSION_TOKEN_KEY)
    if isinstance(token, str):
        _destroy_server_session(token)
    st.session_state.pop(SESSION_USER_KEY, None)
    st.session_state.pop(SESSION_TOKEN_KEY, None)
    st.session_state.pop("_rag_auth_cookie_attempts", None)
    st.session_state.pop("_rag_auth_cookie_checked", None)
    _clear_auth_cookie()
    _persist_portal_auth_token(None)


_AUTH_TOAST_KEY = "rag_auth_toast"


def queue_auth_toast(message: str, kind: str = "success") -> None:
    """Show on the next rerun (after login, logout, or registration)."""
    if kind not in ("success", "error", "info", "warning"):
        kind = "info"
    st.session_state[_AUTH_TOAST_KEY] = (kind, message)


def render_auth_toasts() -> None:
    payload = st.session_state.pop(_AUTH_TOAST_KEY, None)
    if not payload:
        return
    kind, message = payload
    icons = {
        "success": "✅",
        "error": "❌",
        "info": "ℹ️",
        "warning": "⚠️",
    }
    icon = icons.get(kind, "ℹ️")
    try:
        st.toast(message, icon=icon)
    except Exception:
        if kind == "error":
            st.error(message)
        elif kind == "warning":
            st.warning(message)
        else:
            st.success(message)


def current_user() -> Optional[Dict[str, Any]]:
    user = st.session_state.get(SESSION_USER_KEY)
    return user if isinstance(user, dict) else None


def is_logged_in() -> bool:
    return current_user() is not None


def chat_user_id() -> str:
    """Stable id for per-user chat history (separate from demo portal users)."""
    user = current_user()
    if not user:
        return "anonymous"
    em = _normalize_email(str(user.get("email", "")))
    return f"rag_{em}" if em else "rag_anonymous"


def display_name() -> str:
    user = current_user()
    if not user:
        return ""
    return str(user.get("username") or user.get("email") or "")
