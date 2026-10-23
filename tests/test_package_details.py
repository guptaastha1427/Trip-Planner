"""Package catalog detail helpers."""

from services.travel_packages import (
    PACKAGES,
    days_to_day_plan_markdown,
    get_package_detail,
    package_nights_days_badge,
)


def test_package_nights_days_badge():
    assert package_nights_days_badge(1) == "1N/2D"
    assert package_nights_days_badge(5) == "5N/6D"


def test_days_to_day_plan_markdown_includes_day_numbers():
    detail = get_package_detail("weekend_escape")
    assert detail is not None
    text = days_to_day_plan_markdown(detail.days)
    assert "**Day 1:**" in text
    assert "**Day 2:**" in text


def test_each_catalog_package_has_structured_days():
    for pkg in PACKAGES.values():
        detail = get_package_detail(pkg.package_id)
        assert detail is not None
        assert detail.tour_type
        assert detail.night_splits
        assert len(detail.days) >= 1
