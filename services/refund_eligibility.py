"""
Rule-based refund eligibility engine (does not process real payments).

All decisions flow from configurable policies + booking/account state.
UI and chatbot layers must not override these results.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from services.bookings import parse_journey_dt
from services.demo_users import (
    ACCOUNT_BLACKLISTED,
    ACCOUNT_TEMP_RESTRICTED,
    ACCOUNT_UNDER_REVIEW,
)
from services.refund_policy_config import (
    ELIGIBILITY_ELIGIBLE,
    ELIGIBILITY_MANUAL,
    ELIGIBILITY_NOT,
    ELIGIBILITY_PARTIAL,
    REFUND_WORKFLOW_STATUSES,
    get_policy,
)


@dataclass
class RefundEvaluation:
    eligibility: str
    reason: str
    original_amount: float
    cancellation_fee: float
    estimated_refund: float
    currency: str
    next_steps: List[str]
    procedure_steps: List[str]
    processing_time: str
    workflow_status: str
    explanation_detail: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "eligibility": self.eligibility,
            "reason": self.reason,
            "original_amount": self.original_amount,
            "cancellation_fee": self.cancellation_fee,
            "estimated_refund": self.estimated_refund,
            "currency": self.currency,
            "next_steps": self.next_steps,
            "procedure_steps": self.procedure_steps,
            "processing_time": self.processing_time,
            "workflow_status": self.workflow_status,
            "explanation_detail": self.explanation_detail,
        }


def _hours_until_departure(journey: datetime, now: datetime) -> float:
    delta = journey - now
    return delta.total_seconds() / 3600.0


def _round_money(amount: float) -> float:
    return round(max(0.0, amount), 2)


def calculate_refund_amounts(
    booked_amount: float,
    policy,
) -> tuple[float, float]:
    """Return (cancellation_fee, estimated_refund) from policy rates."""
    fee = booked_amount * policy.cancellation_fee_rate
    remainder = booked_amount - fee
    refundable = remainder * policy.max_refund_fraction
    if policy.refundability == "none":
        return _round_money(booked_amount), 0.0
    return _round_money(fee), _round_money(refundable)


def evaluate_refund_request(
    booking: Dict[str, Any],
    user_id: str,
    account_status: str,
    existing_refund_for_booking: Optional[Dict[str, Any]],
    reason: str,
    now: Optional[datetime] = None,
) -> RefundEvaluation:
    """
    Evaluate whether a refund request is allowed and compute estimated amounts.

    Checks: ownership (caller must pass correct booking), booking status,
    departure window, policy, duplicate requests, and account restrictions.
    """
    now = now or datetime.now(timezone.utc).replace(tzinfo=None)
    booked = float(booking.get("booked_amount", 0))
    currency = str(booking.get("currency", "INR"))
    booking_id = booking.get("booking_id", "")
    status = str(booking.get("status", "")).lower()

    policy = get_policy(str(booking.get("policy_id", "")))
    if not policy:
        return RefundEvaluation(
            eligibility=ELIGIBILITY_NOT,
            reason="No refund policy found for this booking.",
            original_amount=booked,
            cancellation_fee=booked,
            estimated_refund=0.0,
            currency=currency,
            next_steps=["Contact support with your booking reference."],
            procedure_steps=_default_procedure(),
            processing_time="N/A",
            workflow_status="Rejected",
            explanation_detail="Missing policy configuration.",
        )

    if booking.get("user_id") != user_id:
        return RefundEvaluation(
            eligibility=ELIGIBILITY_NOT,
            reason="This booking does not belong to the selected account.",
            original_amount=booked,
            cancellation_fee=booked,
            estimated_refund=0.0,
            currency=currency,
            next_steps=["Sign in with the account that made the booking."],
            procedure_steps=_default_procedure(),
            processing_time="N/A",
            workflow_status="Rejected",
            explanation_detail="Ownership check failed.",
        )

    if existing_refund_for_booking:
        return RefundEvaluation(
            eligibility=ELIGIBILITY_NOT,
            reason="A refund request already exists for this booking.",
            original_amount=booked,
            cancellation_fee=booked,
            estimated_refund=0.0,
            currency=currency,
            next_steps=[
                f"Track existing request {existing_refund_for_booking.get('request_id')}."
            ],
            procedure_steps=_default_procedure(),
            processing_time="N/A",
            workflow_status="Rejected",
            explanation_detail="Duplicate submission blocked.",
        )

    if status in ("refunded", "cancelled_refunded"):
        return RefundEvaluation(
            eligibility=ELIGIBILITY_NOT,
            reason="This booking has already been refunded.",
            original_amount=booked,
            cancellation_fee=booked,
            estimated_refund=0.0,
            currency=currency,
            next_steps=["No further refund is available for this booking."],
            procedure_steps=_default_procedure(),
            processing_time="N/A",
            workflow_status="Rejected",
            explanation_detail=f"Booking status: {status}.",
        )

    if status == "completed":
        return RefundEvaluation(
            eligibility=ELIGIBILITY_NOT,
            reason="Travel on this booking is already completed.",
            original_amount=booked,
            cancellation_fee=booked,
            estimated_refund=0.0,
            currency=currency,
            next_steps=["Completed trips are not refundable in this app."],
            procedure_steps=_default_procedure(),
            processing_time="N/A",
            workflow_status="Rejected",
            explanation_detail="Journey marked completed.",
        )

    if status not in ("confirmed", "cancelled"):
        return RefundEvaluation(
            eligibility=ELIGIBILITY_NOT,
            reason=f"Booking status “{status}” is not eligible for a new refund request.",
            original_amount=booked,
            cancellation_fee=booked,
            estimated_refund=0.0,
            currency=currency,
            next_steps=["Verify booking status or contact support."],
            procedure_steps=_default_procedure(),
            processing_time="N/A",
            workflow_status="Rejected",
            explanation_detail=f"Unsupported status: {status}.",
        )

    if account_status == ACCOUNT_BLACKLISTED:
        return RefundEvaluation(
            eligibility=ELIGIBILITY_MANUAL,
            reason="Account is blacklisted pending review; refunds require manual verification.",
            original_amount=booked,
            cancellation_fee=booked,
            estimated_refund=0.0,
            currency=currency,
            next_steps=[
                "Submit an appeal under Account Status.",
                "Open a support ticket with category Account Restriction.",
            ],
            procedure_steps=_manual_procedure(),
            processing_time="Manual review: 5–10 business days",
            workflow_status="Under Review",
            explanation_detail="Blacklisted accounts cannot receive automatic approval.",
        )

    journey = parse_journey_dt(booking)
    hours_left = 9999.0
    if journey:
        j = journey.replace(tzinfo=None) if journey.tzinfo else journey
        hours_left = _hours_until_departure(j, now)

    fee, refund = calculate_refund_amounts(booked, policy)

    if policy.refundability == "none":
        return RefundEvaluation(
            eligibility=ELIGIBILITY_NOT,
            reason="This ticket type is non-refundable under the app policy.",
            original_amount=booked,
            cancellation_fee=fee,
            estimated_refund=0.0,
            currency=currency,
            next_steps=["Review Terms & Policies for non-refundable fares."],
            procedure_steps=_default_procedure(),
            processing_time="N/A",
            workflow_status="Rejected",
            explanation_detail=policy.description,
        )

    if hours_left < policy.min_hours_before_departure:
        return RefundEvaluation(
            eligibility=ELIGIBILITY_NOT,
            reason=(
                f"Cancellation window closed: refunds require at least "
                f"{policy.min_hours_before_departure} hours before departure."
            ),
            original_amount=booked,
            cancellation_fee=fee,
            estimated_refund=0.0,
            currency=currency,
            next_steps=["Consider travel insurance or rescheduling per operator rules."],
            procedure_steps=_default_procedure(),
            processing_time="N/A",
            workflow_status="Rejected",
            explanation_detail=f"Hours until departure: {hours_left:.1f}",
        )

    if policy.refundability == "partial":
        eligibility = ELIGIBILITY_PARTIAL
    else:
        eligibility = ELIGIBILITY_ELIGIBLE

    workflow = "Approved"
    processing = f"{policy.processing_days_min}–{policy.processing_days_max} business days"

    manual_account = account_status in (
        ACCOUNT_UNDER_REVIEW,
        ACCOUNT_TEMP_RESTRICTED,
    )
    if manual_account or reason == "duplicate_booking":
        eligibility = ELIGIBILITY_MANUAL
        workflow = "Under Review"
        processing = "Manual review: 3–7 business days"

    if reason == "duplicate_booking":
        reason_text = "Duplicate booking claims require verification before any refund."
    elif manual_account:
        reason_text = (
            "Your account has a restriction or review flag; "
            "refunds need additional verification."
        )
    elif eligibility == ELIGIBILITY_PARTIAL:
        reason_text = (
            f"Partially eligible under {policy.label}: "
            f"cancellation fee applies per policy."
        )
    else:
        reason_text = f"Eligible under {policy.label} with applicable cancellation fee."

    next_steps = [
        "Confirm the estimated refund amount below.",
        "Submit the request to receive a tracking reference (prototype only).",
    ]
    if workflow == "Under Review":
        next_steps.append(
            "Our team will review within the estimated processing window."
        )

    return RefundEvaluation(
        eligibility=eligibility,
        reason=reason_text,
        original_amount=booked,
        cancellation_fee=fee,
        estimated_refund=refund if eligibility != ELIGIBILITY_NOT else 0.0,
        currency=currency,
        next_steps=next_steps,
        procedure_steps=_default_procedure(),
        processing_time=processing,
        workflow_status=workflow,
        explanation_detail=policy.description,
    )


def _default_procedure() -> List[str]:
    return [
        "Submit refund request with reason and booking reference.",
        "System validates booking and runs eligibility rules (this engine).",
        "Request is approved, rejected, or sent for manual review.",
        "If approved, status moves to Refund Processing.",
        "Completed indicates simulated payout — no real money moves.",
    ]


def _manual_procedure() -> List[str]:
    steps = _default_procedure()
    steps.insert(2, "Fraud / policy team reviews account and booking evidence.")
    return steps


def advance_demo_workflow(current: str) -> Optional[str]:
    """Simulate forward progress for admin / auto-advance."""
    order = list(REFUND_WORKFLOW_STATUSES)
    try:
        idx = order.index(current)
    except ValueError:
        return None
    if idx >= len(order) - 1:
        return None
    return order[idx + 1]
