#!/usr/bin/env python3
"""One-off: remove the word 'demo' from user-facing text (not internal identifiers)."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

KEEP_LINE_SUBSTRINGS = (
    "services.demo_users",
    "services.demo_dashboard",
    "from services.demo",
    "DEMO_USERS",
    "DEMO_BOOKINGS",
    "DEMO_MODE",
    "demo_user_id",
    "demo_uid",
    "demo_dashboard",
    "bootstrap_demo",
    "set_demo_user",
    "get_demo_user",
    "list_demo_users",
    "advance_demo_workflow",
    "render_demo_dashboard",
    "render_demo_user",
    "portal_demo_user",
    "_on_demo_user",
    "_sync_demo_user",
    "demo_bookings.json",
    "admin_demo.py",
    "def get_demo_",
    "def set_demo_",
    "def render_demo_",
    "def bootstrap_demo",
    "def list_demo_",
    "def advance_demo",
    "strip_demo_word",
)


def transform_line(line: str) -> str:
    if any(k in line for k in KEEP_LINE_SUBSTRINGS):
        return line

    s = line
    replacements = [
        ("demo_admin", "travel_admin"),
        ("Completed (Demo)", "Completed"),
        ("Refund Processing (Demo)", "Refund Processing"),
        ("Completed (demo)", "Completed"),
        ("Refund Processing (demo)", "Refund Processing"),
        (".demo@example.com", "@example.com"),
        ("Demo Air Express", "Air Express"),
        ("Demo Railways", "Indian Railways"),
        ("Demo Roadways", "Roadways Express"),
        ("Demo Intl Airways", "Intl Airways"),
        ("Demo Travel Packages", "Travel Packages"),
        ("RR-DEMO-", "RR-SEED-"),
        ("TK-DEMO-", "TK-SEED-"),
        ("AP-DEMO-", "AP-SEED-"),
        ("Demo Blacklist Account", "Blacklist Account"),
        ("Demo dashboard", "Dashboard"),
        ("Demo admin", "Admin"),
        ("Demo Admin", "Admin"),
        ("Demo account", "Account"),
        ("Demo accounts", "Sample accounts"),
        ("Demo user accounts", "User accounts"),
        ("Demo disclaimer", "Disclaimer"),
        ("Demo workflow statuses", "Workflow statuses"),
        ("Admin demo mode", "Admin mode"),
        ("admin demo mode", "admin mode"),
        ("Demo customer accounts", "Customer accounts"),
        ("Demo request", "Refund request"),
        ("Demo login", "Sign-in"),
        ("Demo policy", "Policy"),
        ("Back-office demo", "Back-office"),
        ("Customer demo", "Customer view"),
        ("Book as travel package (demo)", "Book as travel package"),
        ("for class demos", "for training"),
        ("academic demos", "academic use"),
        ("grading demos", "grading"),
        ("to demo the", "to try the"),
        ("in this demo", "in this app"),
        ("this demo", "this app"),
        ("the demo", "the app"),
        ("demo BK-PKG", "BK-PKG"),
        ("(demo evidence)", "(sample evidence)"),
        ("Demo payout", "Payout"),
        ("Demo admin advance", "Admin advance"),
        ("Demo admin approval", "Admin approval"),
        ("Demo admin rejection", "Admin rejection"),
        ("Demo admin update", "Admin update"),
        ("Configurable demo refund", "Configurable refund"),
        ("Demo booking catalog", "Booking catalog"),
        ("confirmed demo package", "confirmed package"),
        ("confirmed demo record", "confirmed record"),
        ("Persistence for demo refunds", "Persistence for refunds"),
        ("Interactive demo admin", "Interactive admin"),
        ("Demo switch between", "Switch between"),
        ("Demo user profiles", "User profiles"),
        ("booking demo travel packages", "booking travel packages"),
        ("Demo travel package catalog", "Travel package catalog"),
    ]
    for old, new in replacements:
        s = s.replace(old, new)

    s = re.sub(r"\s*\([Dd]emo\)", "", s)
    phrase_fixes = [
        (r"\bdemo policy\b", "policy"),
        (r"\bdemo account\b", "account"),
        (r"\bdemo user\b", "user"),
        (r"\bdemo users\b", "users"),
        (r"\bdemo booking\b", "booking"),
        (r"\bdemo bookings\b", "bookings"),
        (r"\bdemo records\b", "records"),
        (r"\bdemo data\b", "sample data"),
        (r"\bdemo state\b", "portal state"),
        (r"\bdemo JSON\b", "local JSON"),
        (r"\bdemo terms\b", "these terms"),
        (r"\bdemo clock\b", "app clock"),
        (r"\bdemo multiplier\b", "pricing multiplier"),
        (r"\bdemo add-on\b", "add-on"),
        (r"\bdemo engine\b", "refund engine"),
        (r"\bdemo rules\b", "policy rules"),
        (r"\bdemo workflow\b", "refund workflow"),
        (r"\bdemo review queue\b", "review queue"),
        (r"\bdemo customers\b", "customers"),
        (r"\bdemo customer\b", "customer"),
        (r"\bdemo amounts\b", "estimated amounts"),
        (r"\bdemo only\b", "prototype only"),
        (r"\bdemo snapshot\b", "snapshot"),
        (r"\bdemo travel packages\b", "travel packages"),
        (r"\bdemo package\b", "package"),
        (r"\bdemo refunds\b", "refunds"),
        (r"\bdemo refund\b", "refund"),
        (r"\bdemo labels\b", "status labels"),
        (r"\bdemo narrative\b", "training scenarios"),
        (r"\bdemo scenarios\b", "sample scenarios"),
        (r"\bdemo profiles\b", "profiles"),
        (r"\bdemo profile\b", "profile"),
        (r"\bdemo evidence\b", "sample evidence"),
        (r"\bfor demos\b", "for training"),
        (r"\bdemo simplicity\b", "prototype simplicity"),
        (r"\bdemo railway-style\b", "railway-style"),
        (r"\bdemo fraction\b", "configured fraction"),
        (r"\bdemo rates\b", "configured rates"),
        (r"\bdemo legal\b", "illustrative legal"),
        (r"\bdemo text\b", "policy text"),
        (r"\bdemo rules at runtime\b", "configured rules at runtime"),
        (r"\bdemo\.\b", "."),
        (r"\bdemo\b", ""),
    ]
    for pat, repl in phrase_fixes:
        s = re.sub(pat, repl, s, flags=re.IGNORECASE)

    s = re.sub(r"  +", " ", s)
    s = re.sub(r" \.", ".", s)
    s = re.sub(r"\( \)", "", s)
    return s


def main() -> None:
    paths = []
    for ext in (".py", ".md", ".json"):
        paths.extend(ROOT.rglob(f"*{ext}"))
    paths.append(ROOT / ".docs")
    for path in paths:
        if "scripts/" in str(path) or path.name == "strip_demo_word.py":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        lines = [transform_line(ln) for ln in text.splitlines(keepends=True)]
        new_text = "".join(lines)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")


if __name__ == "__main__":
    main()
