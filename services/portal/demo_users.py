"""
User profiles for the customer portal (academic prototype — no real auth).

Each profile maps to mock bookings and account scenarios for grading.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# Account status values shown in UI and used by the refund engine.
ACCOUNT_ACTIVE = "active"
ACCOUNT_UNDER_REVIEW = "under_review"
ACCOUNT_TEMP_RESTRICTED = "temporarily_restricted"
ACCOUNT_BLACKLISTED = "blacklisted"

DEMO_USERS: Dict[str, Dict[str, Any]] = {
    "user_alex": {
        "user_id": "user_alex",
        "display_name": "Alex Kumar (default)",
        "email": "alex@example.com",
        "account_status": ACCOUNT_ACTIVE,
        "restriction_notes": [],
    },
    "user_maya": {
        "user_id": "user_maya",
        "display_name": "Maya Sharma (partial / non-refundable mix)",
        "email": "maya@example.com",
        "account_status": ACCOUNT_ACTIVE,
        "restriction_notes": [],
    },
    "user_sam": {
        "user_id": "user_sam",
        "display_name": "Sam Patel (already refunded / completed)",
        "email": "sam@example.com",
        "account_status": ACCOUNT_ACTIVE,
        "restriction_notes": [],
    },
    "user_review": {
        "user_id": "user_review",
        "display_name": "Riya Nair (account under review)",
        "email": "riya@example.com",
        "account_status": ACCOUNT_UNDER_REVIEW,
        "restriction_notes": [
            {
                "code": "unusual_refund_pattern",
                "summary": "Multiple refund requests flagged for verification.",
                "date": "2026-10-01",
                "booking_ref": "BK-FLT-1301",
            }
        ],
    },
    "user_restricted": {
        "user_id": "user_restricted",
        "display_name": "Vikram Singh (temporarily restricted)",
        "email": "vikram@example.com",
        "account_status": ACCOUNT_TEMP_RESTRICTED,
        "restriction_notes": [
            {
                "code": "duplicate_claims",
                "summary": "Repeated duplicate refund claims for the same booking (sample evidence).",
                "date": "2026-09-15",
                "booking_ref": "BK-BUS-3301",
            }
        ],
    },
    "user_blacklisted": {
        "user_id": "user_blacklisted",
        "display_name": "Blacklist Account",
        "email": "blocked@example.com",
        "account_status": ACCOUNT_BLACKLISTED,
        "restriction_notes": [
            {
                "code": "fraudulent_claims",
                "summary": "Documented misuse of refund process after verified review (simulated).",
                "date": "2026-08-20",
                "booking_ref": "BK-FLT-1401",
            }
        ],
    },
}

DEFAULT_USER_ID = "user_alex"


def list_demo_users() -> List[Dict[str, Any]]:
    return list(DEMO_USERS.values())


def get_demo_user(user_id: Optional[str]) -> Dict[str, Any]:
    uid = user_id or DEFAULT_USER_ID
    return DEMO_USERS.get(uid, DEMO_USERS[DEFAULT_USER_ID])


def account_status_label(status: str) -> str:
    labels = {
        ACCOUNT_ACTIVE: "Active",
        ACCOUNT_UNDER_REVIEW: "Under Review",
        ACCOUNT_TEMP_RESTRICTED: "Temporarily Restricted",
        ACCOUNT_BLACKLISTED: "Blacklisted",
    }
    return labels.get(status, status.replace("_", " ").title())
