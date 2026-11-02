"""Support FAQ routing eval."""

from eval.runners.support_faq import run_support_faq_eval


def test_support_routing_accuracy():
    out = run_support_faq_eval()
    assert out["summary"]["total"] >= 15
    assert out["summary"]["routing_accuracy"] >= 0.6
