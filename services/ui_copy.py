"""Strip the word 'demo' from user-visible text (identifiers and stored codes unchanged)."""

from __future__ import annotations

import re

_REPLACEMENTS = [
    ("Completed (Demo)", "Completed"),
    ("Refund Processing (Demo)", "Refund Processing"),
    ("Completed (demo)", "Completed"),
    ("Refund Processing (demo)", "Refund Processing"),
    ("Demo Air Express", "Air Express"),
    ("Demo Railways", "Indian Railways"),
    ("Demo Roadways", "Roadways Express"),
    ("Demo Intl Airways", "Intl Airways"),
    ("Demo Travel Packages", "Travel Packages"),
    ("Demo dashboard", "Dashboard"),
    ("Demo admin", "Admin"),
    ("Demo Admin", "Admin"),
    ("Demo account", "Account"),
    ("Demo accounts", "Accounts"),
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
    ("Support (demo)", "Support"),
    ("demonstration only", "illustration only"),
    ("academic demos", "academic use"),
    ("for class demos", "for training"),
    ("to demo the", "to try the"),
]


def polish_ui_copy(text: str) -> str:
    if not text:
        return text
    s = str(text)
    for old, new in _REPLACEMENTS:
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
        (r"\bdemo snapshot\b", "snapshot"),
        (r"\bdemo travel packages\b", "travel packages"),
        (r"\bdemo package\b", "package"),
        (r"\bdemo refunds\b", "refunds"),
        (r"\bdemo refund\b", "refund"),
        (r"\bdemo labels\b", "status labels"),
        (r"\bdemo scenarios\b", "sample scenarios"),
        (r"\bdemo profiles\b", "profiles"),
        (r"\bdemo profile\b", "profile"),
        (r"\bdemo fraction\b", "configured fraction"),
        (r"\bdemo rates\b", "configured rates"),
        (r"\bdemo text\b", "policy text"),
        (r"\bin this demo\b", "in this app"),
        (r"\bthis demo\b", "this app"),
        (r"\bthe demo\b", "the app"),
        (r"\bfor demos\b", "for training"),
        (r"\bdemo railway-style\b", "railway-style"),
        (r"\bdemo only\b", "prototype only"),
        (r"\bdemo simplicity\b", "prototype simplicity"),
        (r"\bdemo\.\b", "."),
        (r"\bdemo\b", ""),
    ]
    for pat, repl in phrase_fixes:
        s = re.sub(pat, repl, s, flags=re.IGNORECASE)
    s = re.sub(r"  +", " ", s)
    s = re.sub(r" \.", ".", s)
    s = re.sub(r"\(\s*\)", "", s)
    return s
