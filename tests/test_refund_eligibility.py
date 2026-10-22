"""Refund eligibility engine tests (run: python -m tests.test_refund_eligibility)."""

from datetime import datetime

from services.bookings import get_booking
from services.refund_eligibility import evaluate_refund_request
from services.refund_policy_config import ELIGIBILITY_NOT, ELIGIBILITY_PARTIAL


def test_fully_refundable_flex_flight() -> None:
 booking = get_booking("BK-FLT-1001")
 assert booking
 ev = evaluate_refund_request(
 booking,
 "user_alex",
 "active",
 None,
 "change_plans",
 now=datetime(2026, 10, 1, 12, 0, 0),
 )
 assert ev.eligibility == "Eligible"
 assert ev.estimated_refund > 0
 assert ev.cancellation_fee < booking["booked_amount"]


def test_non_refundable_basic_fare() -> None:
 booking = get_booking("BK-FLT-1102")
 assert booking
 ev = evaluate_refund_request(
 booking,
 "user_maya",
 "active",
 None,
 "cancel_travel",
 now=datetime(2026, 10, 1, 12, 0, 0),
 )
 assert ev.eligibility == ELIGIBILITY_NOT
 assert ev.estimated_refund == 0


def test_partial_saver_fare() -> None:
 booking = get_booking("BK-FLT-1101")
 assert booking
 ev = evaluate_refund_request(
 booking,
 "user_maya",
 "active",
 None,
 "change_plans",
 now=datetime(2026, 10, 1, 12, 0, 0),
 )
 assert ev.eligibility == ELIGIBILITY_PARTIAL


def test_too_close_to_departure_bus() -> None:
 booking = get_booking("BK-BUS-3001")
 assert booking
 ev = evaluate_refund_request(
 booking,
 "user_alex",
 "active",
 None,
 "change_plans",
 now=datetime(2026, 10, 25, 20, 0, 0),
 )
 assert ev.eligibility == ELIGIBILITY_NOT


def test_already_refunded() -> None:
 booking = get_booking("BK-FLT-1201")
 assert booking
 ev = evaluate_refund_request(
 booking,
 "user_sam",
 "active",
 None,
 "change_plans",
 now=datetime(2026, 10, 1, 12, 0, 0),
 )
 assert ev.eligibility == ELIGIBILITY_NOT


def test_blacklisted_manual_review() -> None:
 booking = get_booking("BK-FLT-1401")
 assert booking
 ev = evaluate_refund_request(
 booking,
 "user_blacklisted",
 "blacklisted",
 None,
 "change_plans",
 now=datetime(2026, 10, 1, 12, 0, 0),
 )
 assert ev.eligibility == "Manual Review Required"


def main() -> None:
 test_fully_refundable_flex_flight()
 test_non_refundable_basic_fare()
 test_partial_saver_fare()
 test_too_close_to_departure_bus()
 test_already_refunded()
 test_blacklisted_manual_review()
 print("All refund eligibility tests passed.")


if __name__ == "__main__":
 main()
