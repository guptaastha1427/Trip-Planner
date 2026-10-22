"""
Configurable demo refund and cancellation policies by travel mode and ticket type.

These rules are illustrative only — not real operator policies.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class RefundPolicy:
    policy_id: str
    travel_mode: str
    ticket_type: str
    label: str
    refundability: str  # full | partial | none
    # Minimum hours before departure to qualify for any refund
    min_hours_before_departure: int
    # Cancellation fee as fraction of booked_amount (0–1)
    cancellation_fee_rate: float
    # Cap on refundable fraction after fee (1.0 = full remainder)
    max_refund_fraction: float
    processing_days_min: int
    processing_days_max: int
    description: str


POLICIES: Dict[str, RefundPolicy] = {
    "flight_flex": RefundPolicy(
        policy_id="flight_flex",
        travel_mode="flight",
        ticket_type="flex",
        label="Flight — Flex fare",
        refundability="full",
        min_hours_before_departure=24,
        cancellation_fee_rate=0.05,
        max_refund_fraction=1.0,
        processing_days_min=5,
        processing_days_max=10,
        description="Flexible air fare: refundable with a small service fee if cancelled 24+ hours before departure.",
    ),
    "flight_saver": RefundPolicy(
        policy_id="flight_saver",
        travel_mode="flight",
        ticket_type="saver",
        label="Flight — Saver fare",
        refundability="partial",
        min_hours_before_departure=72,
        cancellation_fee_rate=0.35,
        max_refund_fraction=0.65,
        processing_days_min=7,
        processing_days_max=14,
        description="Saver air fare: partial refund with higher cancellation charges.",
    ),
    "flight_basic": RefundPolicy(
        policy_id="flight_basic",
        travel_mode="flight",
        ticket_type="basic",
        label="Flight — Basic / promo fare",
        refundability="none",
        min_hours_before_departure=0,
        cancellation_fee_rate=1.0,
        max_refund_fraction=0.0,
        processing_days_min=0,
        processing_days_max=0,
        description="Promotional basic fare: non-refundable in this demo.",
    ),
    "train_ac3": RefundPolicy(
        policy_id="train_ac3",
        travel_mode="train",
        ticket_type="ac_3_tier",
        label="Train — AC 3-tier",
        refundability="partial",
        min_hours_before_departure=48,
        cancellation_fee_rate=0.15,
        max_refund_fraction=0.85,
        processing_days_min=3,
        processing_days_max=7,
        description="AC train ticket: partial refund per demo railway-style rules.",
    ),
    "train_sleeper": RefundPolicy(
        policy_id="train_sleeper",
        travel_mode="train",
        ticket_type="sleeper",
        label="Train — Sleeper",
        refundability="partial",
        min_hours_before_departure=24,
        cancellation_fee_rate=0.25,
        max_refund_fraction=0.75,
        processing_days_min=3,
        processing_days_max=7,
        description="Sleeper class: lower refund window than AC in this demo.",
    ),
    "bus_semi_sleeper": RefundPolicy(
        policy_id="bus_semi_sleeper",
        travel_mode="bus",
        ticket_type="semi_sleeper",
        label="Bus — Semi-sleeper",
        refundability="partial",
        min_hours_before_departure=12,
        cancellation_fee_rate=0.20,
        max_refund_fraction=0.80,
        processing_days_min=2,
        processing_days_max=5,
        description="Intercity bus semi-sleeper: partial refund if cancelled 12+ hours before departure.",
    ),
    "bus_volvo": RefundPolicy(
        policy_id="bus_volvo",
        travel_mode="bus",
        ticket_type="volvo",
        label="Bus — Volvo AC",
        refundability="full",
        min_hours_before_departure=6,
        cancellation_fee_rate=0.10,
        max_refund_fraction=1.0,
        processing_days_min=2,
        processing_days_max=5,
        description="Premium bus: refundable with moderate fee close to departure (demo).",
    ),
    "package_flex": RefundPolicy(
        policy_id="package_flex",
        travel_mode="package",
        ticket_type="flex",
        label="Travel package — Flex",
        refundability="full",
        min_hours_before_departure=72,
        cancellation_fee_rate=0.08,
        max_refund_fraction=1.0,
        processing_days_min=7,
        processing_days_max=14,
        description="Bundled flight/stay package: refundable with service fee if cancelled 72+ hours before departure (demo).",
    ),
    "package_standard": RefundPolicy(
        policy_id="package_standard",
        travel_mode="package",
        ticket_type="standard",
        label="Travel package — Standard",
        refundability="partial",
        min_hours_before_departure=120,
        cancellation_fee_rate=0.25,
        max_refund_fraction=0.70,
        processing_days_min=10,
        processing_days_max=21,
        description="Standard package fare: partial refund with higher cancellation charges (demo).",
    ),
}

REFUND_REASONS = [
    ("cancel_travel", "Cancellation of travel"),
    ("change_plans", "Change of plans"),
    ("duplicate_booking", "Duplicate booking"),
    ("operator_cancelled", "Operator cancelled service"),
    ("other", "Other reason"),
]

# Workflow statuses for refund requests (simulated processing).
REFUND_WORKFLOW_STATUSES = (
    "Submitted",
    "Under Review",
    "Approved",
    "Rejected",
    "Refund Processing (Demo)",
    "Completed (Demo)",
)

# Eligibility outcomes from the rule engine (before workflow assignment).
ELIGIBILITY_ELIGIBLE = "Eligible"
ELIGIBILITY_PARTIAL = "Partially Eligible"
ELIGIBILITY_NOT = "Not Eligible"
ELIGIBILITY_MANUAL = "Manual Review Required"


def get_policy(policy_id: str) -> Optional[RefundPolicy]:
    return POLICIES.get(policy_id)


def policy_as_dict(policy: RefundPolicy) -> Dict[str, Any]:
    return {
        "policy_id": policy.policy_id,
        "travel_mode": policy.travel_mode,
        "ticket_type": policy.ticket_type,
        "label": policy.label,
        "refundability": policy.refundability,
        "min_hours_before_departure": policy.min_hours_before_departure,
        "cancellation_fee_rate": policy.cancellation_fee_rate,
        "max_refund_fraction": policy.max_refund_fraction,
        "processing_days_min": policy.processing_days_min,
        "processing_days_max": policy.processing_days_max,
        "description": policy.description,
    }
