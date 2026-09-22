"""
Preference Aggregation Service

This is intentionally pure Python with no Django view/serializer dependencies
so it can be tested independently and reused from Celery tasks or the AI planner.

Design principle:
  The LLM should NEVER be asked to "figure out group preferences".
  That is a deterministic calculation that belongs in application code.
  The LLM receives the *output* of this service as structured context.
"""
from collections import Counter
from decimal import Decimal
from statistics import median, stdev
from typing import Any

from trip_preferences.models import MemberPreference


# ────────────────────────────────────────────────────────────────────────────
# Constants – weights / thresholds (easy to change without touching logic)
# ────────────────────────────────────────────────────────────────────────────

# An interest is "popular" if this fraction of members share it
POPULAR_INTEREST_THRESHOLD = 0.5   # ≥50% of members

# An interest is "common" if every member has it
COMMON_INTEREST_THRESHOLD = 1.0

# A preference difference qualifies as a "conflict" if the minority share is >= this
CONFLICT_MIN_SHARE = 0.3            # ≥30% disagree → flag it


def aggregate(trip_id: int) -> dict[str, Any]:
    """
    Given a trip_id, read all MemberPreference rows and return a structured
    aggregation dict that can be serialised straight to JSON.

    Returns:
        {
            "member_count": int,
            "preferences_submitted": int,
            "completion_pct": float,          # 0-100
            "budget": {...},
            "interests": {...},
            "travel_style": {...},
            "transport": {...},
            "accommodation": {...},
            "activity_intensity": {...},
            "diet": {...},
            "conflicts": [...],
        }
    """
    prefs = list(
        MemberPreference.objects.filter(trip_id=trip_id).select_related('user', 'trip')
    )

    # We need the total member count from the TripMember table
    from trips.models import TripMember
    total_members = TripMember.objects.filter(trip_id=trip_id).count()

    if not prefs:
        return {
            "member_count": total_members,
            "preferences_submitted": 0,
            "completion_pct": 0.0,
            "budget": None,
            "interests": None,
            "travel_style": None,
            "transport": None,
            "accommodation": None,
            "activity_intensity": None,
            "diet": None,
            "conflicts": [],
        }

    n = len(prefs)
    conflicts = []

    # ── Budget ─────────────────────────────────────────────────────────────
    max_budgets = [float(p.max_budget) for p in prefs if p.max_budget is not None]
    min_budgets = [float(p.min_budget) for p in prefs if p.min_budget is not None]

    budget_info = None
    if max_budgets:
        median_max = median(max_budgets)
        group_min_acceptable = min(max_budgets)   # The tightest constraint
        members_over_median = sum(1 for b in max_budgets if b < median_max)

        budget_info = {
            "median_max_budget": round(median_max, 2),
            "lowest_max_budget": round(min(max_budgets), 2),
            "highest_max_budget": round(max(max_budgets), 2),
            "group_min_acceptable": round(group_min_acceptable, 2),
            "members_with_budget": len(max_budgets),
            "stddev": round(stdev(max_budgets), 2) if len(max_budgets) > 1 else 0,
        }

        # Flag budget conflict if spread is very wide (>50% above median)
        if max_budgets and budget_info["stddev"] > median_max * 0.5:
            conflicts.append({
                "type": "budget",
                "severity": "warning",
                "message": (
                    f"Large budget spread: lowest ₹{budget_info['lowest_max_budget']:,.0f} "
                    f"vs highest ₹{budget_info['highest_max_budget']:,.0f}. "
                    f"Plan around ₹{group_min_acceptable:,.0f} to include everyone."
                )
            })

    # ── Interests ──────────────────────────────────────────────────────────
    all_interests: list[str] = []
    for p in prefs:
        all_interests.extend(p.interests or [])

    interest_counts = Counter(all_interests)
    popular = [k for k, v in interest_counts.items() if v / n >= POPULAR_INTEREST_THRESHOLD]
    common  = [k for k, v in interest_counts.items() if v / n >= COMMON_INTEREST_THRESHOLD]
    ranked  = [{"interest": k, "count": v, "pct": round(v / n * 100)}
               for k, v in interest_counts.most_common()]

    interests_info = {
        "all_ranked": ranked,
        "popular": popular,        # ≥50% share it
        "common": common,          # 100% share it
    }

    # ── Travel Style ───────────────────────────────────────────────────────
    style_counts = Counter(p.travel_style for p in prefs)
    dominant_style = style_counts.most_common(1)[0][0]
    style_info = {
        "dominant": dominant_style,
        "distribution": dict(style_counts),
    }
    if len(style_counts) > 1:
        minority_share = (n - style_counts.most_common(1)[0][1]) / n
        if minority_share >= CONFLICT_MIN_SHARE:
            conflicts.append({
                "type": "travel_style",
                "severity": "info",
                "message": (
                    f"Mixed travel style preferences: "
                    + ", ".join(f"{v} prefer {k}" for k, v in style_counts.items())
                )
            })

    # ── Transport ──────────────────────────────────────────────────────────
    transport_counts = Counter(p.preferred_transport for p in prefs)
    transport_info = {
        "dominant": transport_counts.most_common(1)[0][0],
        "distribution": dict(transport_counts),
    }

    # ── Accommodation ──────────────────────────────────────────────────────
    acc_counts = Counter(p.accommodation_type for p in prefs)
    accommodation_info = {
        "dominant": acc_counts.most_common(1)[0][0],
        "distribution": dict(acc_counts),
    }

    # ── Activity Intensity ─────────────────────────────────────────────────
    intensity_counts = Counter(p.activity_intensity for p in prefs)
    dominant_intensity = intensity_counts.most_common(1)[0][0]
    intensity_info = {
        "dominant": dominant_intensity,
        "distribution": dict(intensity_counts),
    }
    if len(intensity_counts) > 1:
        minority_count = n - intensity_counts.most_common(1)[0][1]
        if minority_count / n >= CONFLICT_MIN_SHARE:
            conflicts.append({
                "type": "activity_intensity",
                "severity": "warning",
                "message": (
                    f"Activity intensity mismatch: "
                    + ", ".join(f"{v} prefer {k}" for k, v in intensity_counts.items())
                    + ". Itinerary should balance relaxed and active options."
                )
            })

    # ── Diet ───────────────────────────────────────────────────────────────
    diet_counts   = Counter(p.diet_type for p in prefs)
    all_allergies: list[str] = []
    for p in prefs:
        all_allergies.extend(p.food_allergies or [])
    allergy_counts = Counter(all_allergies)

    diet_info = {
        "distribution": dict(diet_counts),
        "most_restrictive": _most_restrictive_diet(diet_counts),
        "allergies": [{"item": k, "count": v} for k, v in allergy_counts.most_common()],
    }

    # Check for vegetarian/vegan vs non-veg conflict
    strict_diet = sum(diet_counts.get(d, 0) for d in ['vegetarian', 'vegan', 'halal'])
    if strict_diet > 0 and diet_counts.get('non_vegetarian', 0) > 0:
        conflicts.append({
            "type": "diet",
            "severity": "warning",
            "message": (
                f"{strict_diet} member(s) have dietary restrictions (vegetarian/vegan/halal). "
                "Restaurant choices must accommodate them."
            )
        })

    return {
        "member_count": total_members,
        "preferences_submitted": n,
        "completion_pct": round(n / total_members * 100, 1) if total_members else 0,
        "budget": budget_info,
        "interests": interests_info,
        "travel_style": style_info,
        "transport": transport_info,
        "accommodation": accommodation_info,
        "activity_intensity": intensity_info,
        "diet": diet_info,
        "conflicts": conflicts,
    }


# ────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ────────────────────────────────────────────────────────────────────────────

_DIET_RESTRICTIVENESS = ['vegan', 'vegetarian', 'halal', 'non_vegetarian']

def _most_restrictive_diet(diet_counts: Counter) -> str:
    """Return the most restrictive diet present so kitchens know the base case."""
    for diet in _DIET_RESTRICTIVENESS:
        if diet_counts.get(diet, 0) > 0:
            return diet
    return 'non_vegetarian'
