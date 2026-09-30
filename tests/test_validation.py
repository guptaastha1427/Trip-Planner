"""Quick tests for itinerary validation (run: python -m tests.test_validation)."""

from services.validation import (
    dedupe_itinerary_pois,
    extract_json,
    validate_itinerary_poi_ids,
    validate_itinerary_unique_pois,
    verify_single_day_unchanged,
)


def main() -> None:
    raw = (
        'Here is the plan:\n```json\n'
        '{"days":[{"day":1,"morning":[{"poi_id":"a","name":"x","why":"y"}],'
        '"afternoon":[],"evening":[]}]}\n```'
    )
    j = extract_json(raw)
    validate_itinerary_poi_ids(j, {"a": {}})

    before = {
        "days": [
            {"day": 1, "morning": [], "afternoon": [], "evening": []},
            {"day": 2, "morning": [], "afternoon": [], "evening": []},
        ]
    }
    after = {
        "days": [
            {"day": 1, "morning": [], "afternoon": [], "evening": []},
            {
                "day": 2,
                "morning": [{"poi_id": "b"}],
                "afternoon": [],
                "evening": [],
            },
        ]
    }
    verify_single_day_unchanged(before, after, 2)

    dup = {
        "days": [
            {
                "day": 1,
                "morning": [{"poi_id": "a"}],
                "afternoon": [{"poi_id": "a"}],
                "evening": [],
            }
        ]
    }
    try:
        validate_itinerary_unique_pois(dup)
        raise AssertionError("expected duplicate validation error")
    except ValueError:
        pass
    dedupe_itinerary_pois(dup)
    validate_itinerary_unique_pois(dup)
    print("validation ok")


if __name__ == "__main__":
    main()
