"""Refund decision table (extends portal tests)."""

from eval.runners.refund_rules import run_refund_rules_eval


def test_refund_decision_table():
    out = run_refund_rules_eval()
    assert out["summary"]["total"] >= 10
    assert out["summary"]["pass_rate"] == 1.0
