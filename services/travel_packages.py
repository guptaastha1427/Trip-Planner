"""Demo travel package catalog and booking prefill helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Any, Dict, List, Optional

PACKAGE_BOOKING_PREFILL_KEY = "package_booking_prefill"
# Each traveler is priced separately (single occupancy, private room — no twin sharing).
PACKAGE_DEFAULT_TRAVELERS = 1
PACKAGE_MAX_TRAVELERS = 8

# Exactly five catalog bundles — all strictly 1 Night / 1 Day.
CATALOG_TERMS_DISPLAY_ORDER: tuple[str, ...] = (
    "weekend_escape",
    "city_explorer",
    "heritage_trail",
    "coastal_bus",
    "custom_trip",
)

@dataclass(frozen=True)
class PackageDay:
    """Structured day row for package detail UI and Terms indexing."""

    day_number: int
    title: str
    hotel: str
    sightseeing: tuple[str, ...]
    meals: tuple[str, ...]
    summary: str = ""


@dataclass(frozen=True)
class PackageDetail:
    """Extended catalog copy for UI expanders and Terms/RAG indexing."""

    highlights: tuple[str, ...]
    day_plan: str
    accommodation: str
    transport: str
    meals: str
    sightseeing: str
    exclusions: str
    cancellation_hint: str
    ideal_for: str
    operator_contact: str
    tour_type: str
    night_splits: tuple[str, ...]
    days: tuple[PackageDay, ...]
    promo_label: str = ""
    list_price_per_person: Optional[float] = None


def package_nights_days_badge(nights: int) -> str:
    """Tour-style duration chip, e.g. 1N/2D or 5N/6D."""
    n = max(1, int(nights))
    return f"{n}N/{n + 1}D"


def days_to_day_plan_markdown(days: tuple[PackageDay, ...]) -> str:
    parts: List[str] = []
    for day in days:
        line = f"**Day {day.day_number}:** {day.title}"
        if day.summary:
            line += f" — {day.summary}"
        parts.append(line)
    return " ".join(parts)


def _catalog_detail(
    *,
    highlights: tuple[str, ...],
    days: tuple[PackageDay, ...],
    tour_type: str,
    night_splits: tuple[str, ...],
    accommodation: str,
    transport: str,
    meals: str,
    sightseeing: str,
    exclusions: str,
    cancellation_hint: str,
    ideal_for: str,
    operator_contact: str,
    promo_label: str = "",
    list_price_per_person: Optional[float] = None,
) -> PackageDetail:
    return PackageDetail(
        highlights=highlights,
        day_plan=days_to_day_plan_markdown(days),
        accommodation=accommodation,
        transport=transport,
        meals=meals,
        sightseeing=sightseeing,
        exclusions=exclusions,
        cancellation_hint=cancellation_hint,
        ideal_for=ideal_for,
        operator_contact=operator_contact,
        tour_type=tour_type,
        night_splits=night_splits,
        days=days,
        promo_label=promo_label,
        list_price_per_person=list_price_per_person,
    )


PACKAGE_DETAILS: Dict[str, PackageDetail] = {
    "weekend_escape": _catalog_detail(
        highlights=(
            "AC Volvo coach Delhi ↔ Nainital",
            "1 night 3★ lake-view hotel (single occupancy)",
            "Breakfast included",
            "Evening Mall Road & Naini Lake leisure time",
        ),
        days=(
            PackageDay(
                1,
                "Delhi → Nainital",
                "3★ lake-view hotel near Mall Road (private room)",
                ("Naini Lake promenade", "Mall Road cafes & local market"),
                ("Dinner on your own",),
                "Morning AC Volvo departure; afternoon check-in and lake walk.",
            ),
            PackageDay(
                2,
                "Nainital → Delhi",
                "Checkout after breakfast",
                ("Optional boat ride (extra)", "Optional Snow View point"),
                ("Breakfast",),
                "Return coach to Delhi by evening.",
            ),
        ),
        tour_type="Coach tour",
        night_splits=("1N Nainital",),
        accommodation="3★ hill property near Mall Road — single occupancy, private room.",
        transport="Round-trip AC coach (approx. 7–8 h each way); seat numbers assigned at boarding (demo).",
        meals="Breakfast on Day 2; other meals on your own unless added at booking.",
        sightseeing="Naini Lake promenade, Mall Road cafes, optional Snow View point (entry fees extra).",
        exclusions="Monument entry, personal insurance, tips, meals except breakfast, optional activities.",
        cancellation_hint="Standard fare: cancel 120+ h before departure for partial refund; Flex: 72+ h (see package_standard / package_flex).",
        ideal_for="Couples and small groups wanting a quick hill break without driving.",
        operator_contact="Demo Travel Packages · support@demo-trip-planner.local",
        promo_label="Early bird · 8% off",
        list_price_per_person=5299.0,
    ),
    "city_explorer": _catalog_detail(
        highlights=(
            "Return train Mumbai ↔ Pune",
            "1 night business hotel near city centre",
            "Half-day guided Pune heritage walk",
            "Museum pass (demo partner venues)",
        ),
        days=(
            PackageDay(
                1,
                "Mumbai → Pune",
                "3★ business hotel near city centre",
                ("Guided heritage walk — Shaniwar Wada area", "Dagdusheth Ganpati"),
                ("Lunch & dinner on your own",),
                "Morning train; hotel check-in; afternoon guided city loop.",
            ),
            PackageDay(
                2,
                "Pune → Mumbai",
                "Checkout morning",
                ("Raja Dinkar Kelkar Museum (pass included)",),
                ("Breakfast optional add-on",),
                "Return train to Mumbai.",
            ),
        ),
        tour_type="Rail & city tour",
        night_splits=("1N Pune",),
        accommodation="3★ city hotel — breakfast optional add-on in real ops; demo includes room only.",
        transport="Reserved train berths (SL/3A mix in demo data); local auto/cab for tour start point.",
        meals="Not included except where noted on voucher; cafés on MG Road recommended.",
        sightseeing="Shaniwar Wada, Dagdusheth Ganpati, Raja Dinkar Kelkar Museum (pass).",
        exclusions="Train upgrades, meals, monument audio guides, late checkout.",
        cancellation_hint="Package policies apply; Flex tier recommended for date changes within 72 h window.",
        ideal_for="Weekend urban explorers and history buffs.",
        operator_contact="Demo Travel Packages · support@demo-trip-planner.local",
    ),
    "heritage_trail": _catalog_detail(
        highlights=(
            "AC coach Delhi ↔ Jaipur",
            "1 night 3★ heritage-style hotel",
            "Breakfast included",
            "Guided Amber Fort & Hawa Mahal circuit",
        ),
        days=(
            PackageDay(
                1,
                "Delhi → Jaipur",
                "3★ heritage-style hotel near MI Road",
                ("Hawa Mahal façade & Old City photo stop",),
                ("Dinner on your own",),
                "Coach to Jaipur; afternoon Pink City highlights.",
            ),
            PackageDay(
                2,
                "Jaipur → Delhi",
                "Checkout after breakfast",
                ("Guided Amber Fort visit", "Optional Jantar Mantar (ticket extra)"),
                ("Breakfast",),
                "Morning fort circuit; return coach to Delhi.",
            ),
        ),
        tour_type="Heritage guided",
        night_splits=("1N Jaipur",),
        accommodation="3★ hotel near MI Road — heritage décor; single occupancy.",
        transport="AC coach with scheduled rest stop; local guide meets at fort gate.",
        meals="Breakfast on Day 2; lunch boxes available for purchase on coach.",
        sightseeing="Amber Fort, Hawa Mahal façade, optional Jantar Mantar (ticket extra).",
        exclusions="Fort elephant rides, camera fees at monuments, dinners, personal shopping.",
        cancellation_hint="Monument closures (maintenance) do not auto-qualify for refund — see Terms duplicate-booking rules.",
        ideal_for="First-time visitors to the Pink City with limited time.",
        operator_contact="Demo Travel Packages · support@demo-trip-planner.local",
        promo_label="Popular choice",
    ),
    "coastal_bus": _catalog_detail(
        highlights=(
            "Ferry + shared transfers Mumbai ↔ Alibaug",
            "1 night beach-side resort room",
            "Breakfast included",
            "Beach time or Kolaba Fort visit",
        ),
        days=(
            PackageDay(
                1,
                "Mumbai → Alibaug",
                "Beach-side resort (garden or sea-facing at check-in)",
                ("Sunset beach time", "Local market stroll"),
                ("Dinner à la carte nearby",),
                "Ferry and resort shuttle; check-in and beach leisure.",
            ),
            PackageDay(
                2,
                "Alibaug → Mumbai",
                "Checkout after breakfast",
                ("Kolaba Fort visit (tide-dependent)",),
                ("Breakfast",),
                "Ferry back to Mumbai Gateway.",
            ),
        ),
        tour_type="Coastal getaway",
        night_splits=("1N Alibaug",),
        accommodation="Beach resort — garden or sea-facing category assigned at check-in (demo).",
        transport="Ferry tickets + resort shuttle from jetty; no private car included.",
        meals="Breakfast included; seafood dinners à la carte nearby.",
        sightseeing="Alibaug beach, Kolaba Fort (tide-dependent access), local market.",
        exclusions="Water sports, ferry upgrades, alcohol, travel insurance.",
        cancellation_hint="Weather-related ferry cancellations trigger manual review in the refund engine.",
        ideal_for="Beach lovers and short coastal escapes from Mumbai.",
        operator_contact="Demo Travel Packages · support@demo-trip-planner.local",
    ),
    "custom_trip": _catalog_detail(
        highlights=(
            "Built from Trip Planner destination & days",
            "1 night hotel at your chosen city",
            "Local transfers (demo sedan)",
            "PDF itinerary export bundled",
        ),
        days=(
            PackageDay(
                1,
                "Arrival at your destination",
                "3★ or equivalent at Trip Planner city",
                ("Follow your AI itinerary stops",),
                ("Meals per your plan",),
                "Local sedan transfers; anchor night at destination.",
            ),
            PackageDay(
                2,
                "Departure",
                "Checkout",
                ("Optional morning activity from planner",),
                ("Breakfast not included by default",),
                "Use Trip Planner to design stops, then book this bundle.",
            ),
        ),
        tour_type="Customizable",
        night_splits=("1N at destination",),
        accommodation="3★ or equivalent at Trip Planner destination — category illustrative only.",
        transport="Local transfers airport/station ↔ hotel; inter-city left to your planner choices.",
        meals="Not included unless your itinerary notes food stops (informational only).",
        sightseeing="Follows your AI itinerary — not a fixed guided tour unless you add catalog tickets separately.",
        exclusions="Flights/trains to destination, attraction tickets, guide fees, trip insurance.",
        cancellation_hint="Highest base price tier; Flex fare advised when dates may change.",
        ideal_for="Travelers who already planned a city on Trip Planner and want a demo package record.",
        operator_contact="Demo Travel Packages · support@demo-trip-planner.local",
    ),
}


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


def catalog_route_label(pkg: TravelPackage) -> str:
    """Public alias for UI summaries."""
    return _catalog_typical_route(pkg)


def build_package_fare_tiers_markdown() -> str:
    """Standard vs Flex — pricing formula, examples, and linked refund policies (Terms/RAG)."""
    from services.refund_policy_config import POLICIES

    std_tier = FARE_TIERS["standard"]
    flex_tier = FARE_TIERS["flex"]
    std_pol = POLICIES[std_tier[0]]
    flex_pol = POLICIES[flex_tier[0]]
    std_mult = float(std_tier[2])
    flex_mult = float(flex_tier[2])
    flex_premium_pct = round((flex_mult - 1.0) * 100)

    sample_pkg = PACKAGES["weekend_escape"]
    sample = estimate_package_breakdown(sample_pkg, 2, "standard", nights=1)
    sample_flex = estimate_package_breakdown(sample_pkg, 2, "flex", nights=1)

    return f"""
### Package fare types — Standard vs Flex (pricing & refunds)

Every **Book package** confirmation stores a **fare type** that controls both the **price estimate** at booking time and the **refund policy** (`package_standard` or `package_flex`) used by the refund engine.

| | **Standard** | **Flex** |
|---|--------------|----------|
| **UI label** | {std_tier[3]} | {flex_tier[3]} |
| **Policy ID** | `{std_pol.policy_id}` | `{flex_pol.policy_id}` |
| **Price multiplier** | **{std_mult:.2f}×** (base catalog rate) | **{flex_mult:.2f}×** (+{flex_premium_pct}% vs Standard) |
| **Refundability** | {std_pol.refundability.title()} | {flex_pol.refundability.title()} |
| **Cancel at least** | **{std_pol.min_hours_before_departure} hours** ({std_pol.min_hours_before_departure // 24} days) before departure | **{flex_pol.min_hours_before_departure} hours** ({flex_pol.min_hours_before_departure // 24} days) before departure |
| **Cancellation fee** | **{std_pol.cancellation_fee_rate * 100:.0f}%** of booked amount | **{flex_pol.cancellation_fee_rate * 100:.0f}%** of booked amount |
| **Max refundable fraction** | **{std_pol.max_refund_fraction * 100:.0f}%** of amount after fee (demo cap) | **{flex_pol.max_refund_fraction * 100:.0f}%** |
| **Processing time (demo)** | {std_pol.processing_days_min}–{std_pol.processing_days_max} days | {flex_pol.processing_days_min}–{flex_pol.processing_days_max} days |

**How the booking estimate is calculated (demo math):**

1. **Base subtotal** = package **base price per traveler** × **number of travelers** (each traveler: single occupancy).
2. **Fare adjustment** = base subtotal × (**multiplier − 1**). Standard multiplier is 1.0 (no adjustment). Flex adds **{flex_premium_pct}%** on top of base subtotal.
3. **Night add-on** = **₹1,200 × max(0, nights − included nights) × travelers** (included nights match the catalog bundle, usually **1**).
4. **Total** = base subtotal × multiplier + night add-on. **Per traveler** = total ÷ travelers.

**Worked example — {sample_pkg.name} (`{sample_pkg.package_id}`), 2 travelers, 1 night:**

- Catalog base: **₹{sample_pkg.base_price_per_person:,.0f}** / person → base subtotal **₹{sample['base_subtotal']:,.0f}**.
- **Standard total:** **₹{sample['total']:,.0f}** (₹{sample['per_person']:,.0f} / person).
- **Flex total:** **₹{sample_flex['total']:,.0f}** (₹{sample_flex['per_person']:,.0f} / person) — includes **₹{sample_flex['fare_adjustment']:,.0f}** fare premium.

**When to choose which fare:**

- **Standard** — Lowest upfront demo price; acceptable if your dates are firm and you may not need a refund.
- **Flex** — Pay more at booking for **full** refundability (subject to the **{flex_pol.min_hours_before_departure}-hour** window and **{flex_pol.cancellation_fee_rate * 100:.0f}%** service fee in the demo engine).

Policy descriptions: *{std_pol.description}* · *{flex_pol.description}*
""".strip()


def build_travel_package_catalog_footer_markdown() -> str:
    return (
        "All catalog packages are **1 Night / 1 Day** only (depart Day 1, overnight, return Day 2). "
        "Prices are **estimated** at booking time (travelers, fare type). "
        "**No payment gateway** is connected.\n\n"
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
        "one overnight stay, return on Day 2 (evening). Base prices are **per traveler** (single occupancy, private room) in INR.\n\n"
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


def get_package_detail(package_id: str) -> Optional[PackageDetail]:
    return PACKAGE_DETAILS.get(package_id)


def package_includes_summary(package_id: str) -> str:
    pkg = PACKAGES.get(package_id)
    return _PACKAGE_INCLUDES_SUMMARY.get(
        package_id, pkg.tagline if pkg else ""
    )


def package_detail_markdown(pkg: TravelPackage) -> str:
    """Single-package reference block for Terms indexing and UI."""
    detail = PACKAGE_DETAILS.get(pkg.package_id)
    includes = _PACKAGE_INCLUDES_SUMMARY.get(pkg.package_id, pkg.tagline)
    route = _catalog_typical_route(pkg)
    price = f"₹{pkg.base_price_per_person:,.0f}"
    lines = [
        f"### Package: {pkg.name} (`{pkg.package_id}`)",
        "",
        f"**Tagline:** {pkg.tagline}",
        f"**Typical route:** {route}",
        f"**Duration:** {package_duration_label(pkg.nights)}",
        f"**Base price (demo, per traveler, single occupancy):** {price}",
        f"**Operator:** {pkg.operator}",
        f"**Includes (summary):** {includes}",
        f"**Include codes:** {', '.join(pkg.includes)}",
        "",
    ]
    if detail:
        splits = ", ".join(detail.night_splits) if detail.night_splits else ""
        lines.extend(
            [
                f"**Tour type:** {detail.tour_type}",
                f"**Night split:** {splits}" if splits else "",
                f"**Duration badge:** {package_nights_days_badge(pkg.nights)}",
                "**Highlights:**",
                *[f"- {h}" for h in detail.highlights],
                "",
                f"**Sample itinerary:** {detail.day_plan}",
                f"**Accommodation:** {detail.accommodation}",
                f"**Transport:** {detail.transport}",
                f"**Meals:** {detail.meals}",
                f"**Sightseeing:** {detail.sightseeing}",
                f"**Exclusions:** {detail.exclusions}",
                f"**Cancellation / refunds:** {detail.cancellation_hint}",
                f"**Ideal for:** {detail.ideal_for}",
                f"**Contact (demo):** {detail.operator_contact}",
                "",
            ]
        )
    return "\n".join(lines)


def build_travel_package_catalog_details_markdown() -> str:
    """Per-package sections — improves RAG chunk retrieval for package questions."""
    parts = [
        "### Travel package catalog — detailed descriptions",
        "",
        "Use this section when users ask what is included, itinerary, hotels, transport, "
        "meals, exclusions, or cancellation rules for a specific demo package.",
        "",
    ]
    for pid in CATALOG_TERMS_DISPLAY_ORDER:
        pkg = PACKAGES[pid]
        parts.append(package_detail_markdown(pkg))
    return "\n".join(parts)


def build_travel_package_catalog_markdown() -> str:
    """Full catalog section text for Terms knowledge base."""
    return (
        build_travel_package_catalog_table_markdown()
        + "\n\n"
        + build_package_fare_tiers_markdown()
        + "\n\n"
        + build_travel_package_catalog_details_markdown()
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
    """Demo pricing — per-traveler rate × headcount, nights, package, and fare tier."""
    tier = FARE_TIERS.get(fare_tier, FARE_TIERS["standard"])
    multiplier = float(tier[2])
    n = int(nights if nights is not None else package.nights)
    included_nights = int(package.nights)
    travelers = max(1, min(PACKAGE_MAX_TRAVELERS, int(travelers)))
    base_subtotal = package.base_price_per_person * travelers
    fare_adjustment = base_subtotal * (multiplier - 1.0)
    extra_nights = max(0, n - included_nights)
    nights_extra = extra_nights * 1200.0 * travelers
    total = base_subtotal * multiplier + nights_extra
    return {
        "base_subtotal": round(base_subtotal, 2),
        "fare_adjustment": round(fare_adjustment, 2),
        "nights_extra": round(nights_extra, 2),
        "extra_nights": extra_nights,
        "included_nights": included_nights,
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
