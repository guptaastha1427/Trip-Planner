"""Quick tests for itinerary validation (run: python -m tests.test_validation)."""

from services.core.validation import (
    dedupe_itinerary_pois,
    extract_json,
    validate_itinerary_poi_ids,
    validate_itinerary_unique_pois,
    verify_single_day_unchanged,
)


def main() -> None:
    raw = ( #extract the JSON from the raw text.
        'Here is the plan:\n```json\n'
        '{"days":[{"day":1,"morning":[{"poi_id":"a","name":"x","why":"y"}],'
        '"afternoon":[],"evening":[]}]}\n```'
    )
    j = extract_json(raw) #extract the JSON from the raw text.
    validate_itinerary_poi_ids(j, {"a": {}}) #validate the itinerary POIs.

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
    verify_single_day_unchanged(before, after, 2) #verify the single day unchanged.

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
    #try to validate the itinerary with duplicate POIs, should raise an error.
    try:
        validate_itinerary_unique_pois(dup)
        raise AssertionError("expected duplicate validation error")
    except ValueError:
        pass
    dedupe_itinerary_pois(dup) #dedupe the itinerary POIs.
    validate_itinerary_unique_pois(dup) #validate the itinerary POIs again, should not raise an error.
    print("validation ok")


if __name__ == "__main__":
    main()
