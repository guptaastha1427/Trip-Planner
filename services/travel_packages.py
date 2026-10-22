"""Demo travel package catalog and booking prefill helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Any, Dict, List, Optional

PACKAGE_BOOKING_PREFILL_KEY = "package_booking_prefill"

# Exactly five catalog bundles — all strictly 1 Night / 1 Day.
CATALOG_TERMS_DISPLAY_ORDER: tuple[str, ...] = (
    "weekend_escape",
    "city_explorer",
    "heritage_trail",
    "coastal_bus",
    "custom_trip",
)

_PACKAGE_INCLUDES_SUMMARY: Dict[str, str] = {
    "weekend_escape": (
        "AC coach round-trip, 1 night 3★ hill hotel, breakfast, Nainital Lake & Mall Road leisure"
    ),
    "city_explorer": (
        "Train round-trip, 1 night hotel, guided Pune city tour, museum pass"
    ),
    "heritage_trail": (
        "AC coach round-trip, 1 night 3★ stay, breakfast, guided Amber Fort & Hawa Mahal "
        "(monument entry fees extra where applicable)"
    ),
    "coastal_bus": (
        "Ferry + local transfers, 1 night beach-side stay, breakfast, Kolaba Fort or beach time"
    ),
    "custom_trip": (
        "1 night hotel, local transfers, bundle built from your Trip Planner destination + itinerary PDF"
    ),
}


@dataclass(frozen=True)
class TravelPackage:
    package_id: str
    name: str
    tagline: str
    default_origin: str
    default_destination: str
    nights: int
    base_price_per_person: float
    includes: tuple[str, ...]
    operator: str = "Demo Travel Packages"


PACKAGES: Dict[str, TravelPackage] = {
    "weekend_escape": TravelPackage(
        package_id="weekend_escape",
        name="Weekend Escape",
        tagline="1 night hill break — coach, hotel & lake time",
        default_origin="Delhi",
        default_destination="Nainital",
        nights=1,
        base_price_per_person=4899.0,
        includes=("bus", "hotel", "breakfast", "lake_leisure"),
    ),
    "city_explorer": TravelPackage(
        package_id="city_explorer",
        name="City Explorer",
        tagline="1 night — train, hotel & guided Pune tour",
        default_origin="Mumbai",
        default_destination="Pune",
        nights=1,
        base_price_per_person=6499.0,
        includes=("train", "hotel", "city_tour", "museum_pass"),
    ),
    "heritage_trail": TravelPackage(
        package_id="heritage_trail",
        name="Heritage Trail",
        tagline="1 night Pink City — coach, hotel & fort circuit",
        default_origin="Delhi",
        default_destination="Jaipur",
        nights=1,
        base_price_per_person=5499.0,
        includes=("bus", "hotel", "breakfast", "guided_sightseeing"),
    ),
    "coastal_bus": TravelPackage(
        package_id="coastal_bus",
        name="Coastal Bus Getaway",
        tagline="1 night coast — ferry, beach stay & breakfast",
        default_origin="Mumbai",
        default_destination="Alibaug",
        nights=1,
        base_price_per_person=3999.0,
        includes=("ferry", "hotel", "breakfast", "beach_time"),
    ),
    "custom_trip": TravelPackage(
        package_id="custom_trip",
        name="Custom trip bundle",
        tagline="1 night — build from your Trip Planner destination",
        default_origin="Your city",
        default_destination="Your destination",
        nights=1,
        base_price_per_person=9999.0,
        includes=("hotel", "local_transfer", "itinerary_pdf"),
    ),
}

FARE_TIERS = {
    "flex": ("package_flex", "flex", 1.12, "Flex — easier refunds"),
    "standard": ("package_standard", "standard", 1.0, "Standard — lower base price"),
}


def list_packages() -> List[TravelPackage]:
    return [PACKAGES[pid] for pid in CATALOG_TERMS_DISPLAY_ORDER]


def package_duration_label(nights: int) -> str:
    if nights == 1:
        return "1 Night / 1 Day"
    return f"{int(nights)} nights"


def _catalog_typical_route(pkg: TravelPackage) -> str:
    if pkg.package_id == "custom_trip":
        return "Your Trip Planner cities"
    origin = pkg.default_origin.split("(")[0].strip()
    dest = pkg.default_destination.split("(")[0].strip()
    return f"{origin} → {dest}"


def build_travel_package_catalog_footer_markdown() -> str:
    return (
        "All catalog packages are **1 Night / 1 Day** only (depart Day 1, overnight, return Day 2). "
        "Prices are **estimated** at booking time (travelers, fare type). "
        "**No payment gateway** is connected.\n\n"
        "### Fare types (packages)\n\n"
        "- **Standard** — Lower base multiplier; stricter cancellation window "
        "(**package_standard** policy).\n"
        "- **Flex** — Higher base multiplier (~12% in demo math); more generous refund rules "
        "(**package_flex**).\n\n"
        "### Non-package travel inventory\n\n"
        "Demo users also have **catalog tickets** (flights, trains, buses) such as "
        "`BK-FLT-*`, `BK-TRN-*`, `BK-BUS-*`\n"
        "with mode-specific refund policies — see **Bookings, refunds & legal** tab and "
        "the policy comparison table.\n"
    )


def build_travel_package_catalog_table_markdown() -> str:
    """Markdown table for RAG indexing (one table per markdown block)."""
    header = (
        "### Catalog packages (illustrative INR pricing)\n\n"
        "**Duration:** every row is **1 Night / 1 Day** — depart on Day 1 (morning or afternoon), "
        "one overnight stay, return on Day 2 (evening). Base prices are per person (twin sharing) in INR.\n\n"
        "| Package ID | Name | Typical route | Duration | Base / person (demo) | "
        "Includes (summary) |\n"
        "|------------|------|---------------|----------|----------------------|"
        "-------------------|\n"
    )
    rows: List[str] = []
    for pid in CATALOG_TERMS_DISPLAY_ORDER:
        pkg = PACKAGES[pid]
        price = f"₹{pkg.base_price_per_person:,.0f}"
        includes = _PACKAGE_INCLUDES_SUMMARY.get(pid, pkg.tagline)
        rows.append(
            f"| `{pkg.package_id}` | {pkg.name} | {_catalog_typical_route(pkg)} | "
            f"{package_duration_label(pkg.nights)} | {price} | {includes} |"
        )
    return header + "\n".join(rows)


def build_travel_package_catalog_markdown() -> str:
    """Full catalog section text for Terms knowledge base."""
    return (
        build_travel_package_catalog_table_markdown()
        + "\n\n"
        + build_travel_package_catalog_footer_markdown()
    )


def catalog_rows_for_ui() -> List[Dict[str, str]]:
    """Tabular catalog for Streamlit ``st.dataframe`` on Terms pages."""
    out: List[Dict[str, str]] = []
    for pid in CATALOG_TERMS_DISPLAY_ORDER:
        pkg = PACKAGES[pid]
        out.append(
            {
                "Package ID": pkg.package_id,
                "Name": pkg.name,
                "Typical route": _catalog_typical_route(pkg),
                "Duration": package_duration_label(pkg.nights),
                "Base / person (INR)": f"₹{pkg.base_price_per_person:,.0f}",
                "Includes (summary)": _PACKAGE_INCLUDES_SUMMARY.get(pid, pkg.tagline),
            }
        )
    return out


def get_package(package_id: str) -> Optional[TravelPackage]:
    return PACKAGES.get(package_id)


def estimate_package_breakdown(
    package: TravelPackage,
    travelers: int,
    fare_tier: str,
    nights: Optional[int] = None,
) -> Dict[str, float]:
    """Demo pricing — updates with travelers, nights, package, and fare tier."""
    tier = FARE_TIERS.get(fare_tier, FARE_TIERS["standard"])
    multiplier = float(tier[2])
    n = int(nights if nights is not None else package.nights)
    travelers = max(1, int(travelers))
    base_subtotal = package.base_price_per_person * travelers
    fare_adjustment = base_subtotal * (multiplier - 1.0)
    nights_extra = max(0, n - 2) * 1200.0 * travelers
    total = base_subtotal * multiplier + nights_extra
    return {
        "base_subtotal": round(base_subtotal, 2),
        "fare_adjustment": round(fare_adjustment, 2),
        "nights_extra": round(nights_extra, 2),
        "total": round(total, 2),
        "per_person": round(total / travelers, 2),
        "nights": n,
        "travelers": travelers,
    }


def estimate_package_total(
    package: TravelPackage,
    travelers: int,
    fare_tier: str,
    nights: Optional[int] = None,
) -> float:
    return estimate_package_breakdown(package, travelers, fare_tier, nights)["total"]


def package_booking_prefill_payload(
    *,
    origin: str,
    destination: str,
    trip_days: int,
    package_id: str = "custom_trip",
) -> Dict[str, Any]:
    return {
        "package_id": package_id,
        "origin": origin.strip() or "Your city",
        "destination": destination.strip() or "Your destination",
        "nights": 1,
    }


def journey_iso(departure: date, hour: int = 9, minute: int = 0) -> str:
    return datetime.combine(departure, time(hour, minute)).isoformat(timespec="minutes")
