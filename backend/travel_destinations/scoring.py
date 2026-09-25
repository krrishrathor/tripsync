"""
Destination Compatibility Scoring Engine
=========================================

This is intentionally 100% deterministic Python — no LLM calls.

Given the output of the preference aggregation service and a list of
Destination objects, it scores each destination and returns a ranked list
with per-factor breakdowns and conflict explanations.

SCORING FORMULA
---------------
overall = (
    budget_score        * WEIGHT_BUDGET        +   # 0.30
    interest_score      * WEIGHT_INTEREST      +   # 0.25
    duration_score      * WEIGHT_DURATION      +   # 0.15
    activity_score      * WEIGHT_ACTIVITY      +   # 0.15
    transport_score     * WEIGHT_TRANSPORT     +   # 0.10
    accommodation_score * WEIGHT_ACCOMMODATION +   # 0.05
)

All individual scores are 0.0 – 1.0.
overall score is returned as a 0 – 100 integer for display.

WEIGHTS — declared as module constants so they are:
  (a) documented in one place
  (b) easy to tune without touching logic
  (c) visible in interview / code review
"""
import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Any

logger = logging.getLogger(__name__)

# ── Configurable weights (must sum to 1.0) ───────────────────────────────────
WEIGHT_BUDGET        = 0.30
WEIGHT_INTEREST      = 0.25
WEIGHT_DURATION      = 0.15
WEIGHT_ACTIVITY      = 0.15
WEIGHT_TRANSPORT     = 0.10
WEIGHT_ACCOMMODATION = 0.05

assert abs(
    WEIGHT_BUDGET + WEIGHT_INTEREST + WEIGHT_DURATION +
    WEIGHT_ACTIVITY + WEIGHT_TRANSPORT + WEIGHT_ACCOMMODATION - 1.0
) < 1e-9, "Scoring weights must sum to 1.0"


@dataclass
class FactorScore:
    score: float          # 0.0 – 1.0
    reason: str           # Human-readable explanation shown in UI


@dataclass
class DestinationScore:
    destination_id: int
    destination_name: str
    overall: int          # 0 – 100
    budget: FactorScore
    interest: FactorScore
    duration: FactorScore
    activity: FactorScore
    transport: FactorScore
    accommodation: FactorScore
    conflicts: list[str] = field(default_factory=list)
    highlights: list[str] = field(default_factory=list)


def score_destinations(
    aggregated_prefs: dict[str, Any],
    destinations: list,
    trip_start_date: date | None = None,
    trip_end_date: date | None = None,
) -> list[DestinationScore]:
    """
    Score and rank all active destinations against the group's aggregated
    preferences.

    Args:
        aggregated_prefs: Output dict from trip_preferences.aggregation.aggregate()
        destinations:     Queryset / list of travel_destinations.Destination ORM objects
        trip_start_date:  Optional trip start for seasonal scoring
        trip_end_date:    Optional trip end for duration scoring

    Returns:
        List of DestinationScore, sorted by overall score descending.
    """
    trip_duration_days = None
    if trip_start_date and trip_end_date:
        delta = trip_end_date - trip_start_date
        trip_duration_days = delta.days

    trip_month = trip_start_date.month if trip_start_date else None

    results = []
    for dest in destinations:
        try:
            ds = _score_one(aggregated_prefs, dest, trip_duration_days, trip_month)
            results.append(ds)
        except Exception as exc:
            logger.error("Error scoring destination %s: %s", dest.name, exc)

    results.sort(key=lambda d: d.overall, reverse=True)
    return results


# ─────────────────────────────────────────────────────────────────────────────
# Private helpers
# ─────────────────────────────────────────────────────────────────────────────

def _score_one(
    agg: dict,
    dest,
    trip_duration_days: int | None,
    trip_month: int | None,
) -> DestinationScore:

    conflicts  = []
    highlights = []

    # ── 1. Budget score ───────────────────────────────────────────────────────
    budget_factor = _score_budget(agg, dest, conflicts, highlights)

    # ── 2. Interest score ─────────────────────────────────────────────────────
    interest_factor = _score_interests(agg, dest, conflicts, highlights)

    # ── 3. Duration score ─────────────────────────────────────────────────────
    duration_factor = _score_duration(dest, trip_duration_days, conflicts)

    # ── 4. Activity intensity score ────────────────────────────────────────────
    activity_factor = _score_activity(agg, dest, conflicts, highlights)

    # ── 5. Transport score ────────────────────────────────────────────────────
    transport_factor = _score_transport(agg, dest, conflicts)

    # ── 6. Accommodation score ────────────────────────────────────────────────
    accommodation_factor = _score_accommodation(agg, dest, conflicts)

    # ── 7. Seasonal bonus / penalty (applied to overall, not a separate factor)
    seasonal_mult = _seasonal_multiplier(dest, trip_month)

    # ── Weighted sum ──────────────────────────────────────────────────────────
    raw = (
        budget_factor.score        * WEIGHT_BUDGET        +
        interest_factor.score      * WEIGHT_INTEREST      +
        duration_factor.score      * WEIGHT_DURATION      +
        activity_factor.score      * WEIGHT_ACTIVITY      +
        transport_factor.score     * WEIGHT_TRANSPORT     +
        accommodation_factor.score * WEIGHT_ACCOMMODATION
    ) * seasonal_mult

    overall = round(min(max(raw, 0.0), 1.0) * 100)

    return DestinationScore(
        destination_id=dest.id,
        destination_name=dest.name,
        overall=overall,
        budget=budget_factor,
        interest=interest_factor,
        duration=duration_factor,
        activity=activity_factor,
        transport=transport_factor,
        accommodation=accommodation_factor,
        conflicts=conflicts,
        highlights=highlights,
    )


def _score_budget(agg, dest, conflicts, highlights) -> FactorScore:
    """
    Compare the group's planning budget per person per day against the
    destination's estimated daily cost range.

    We use the group's minimum acceptable max_budget (the tightest wallet)
    divided by the trip duration to get a per-day budget.

    If no budget data: neutral score 0.6 (don't penalise groups that
    haven't filled budgets yet).
    """
    if not agg.get('budget'):
        return FactorScore(0.6, "No budget data submitted yet.")

    group_max = agg['budget']['group_min_acceptable']  # tightest wallet
    dest_min  = dest.estimated_daily_cost_min
    dest_max  = dest.estimated_daily_cost_max
    dest_avg  = dest.estimated_daily_cost_avg

    # We assume a 5-day trip as default if no dates provided
    # (per-day budget is what matters for destination scoring)
    # The raw comparison: can the tightest member afford a day here?

    if group_max >= dest_max:
        # Comfortably within budget for everyone
        score = 1.0
        highlights.append(f"Within budget for all members (dest avg ₹{dest_avg:,}/day)")
    elif group_max >= dest_avg:
        # Mid-range affordable
        score = 0.8
        highlights.append(f"Affordable at mid range (dest avg ₹{dest_avg:,}/day)")
    elif group_max >= dest_min:
        # Can do it budget style
        score = 0.55
        conflicts.append(
            f"Budget is tight — some members may need to stay at budget options "
            f"(cheapest ~₹{dest_min:,}/day, member ceiling ₹{group_max:,}/day)"
        )
    else:
        # Beyond the tightest budget
        score = max(0.1, 1 - (dest_min - group_max) / dest_min)
        conflicts.append(
            f"Over budget for {_members_over(agg, dest_min)} member(s): "
            f"min cost ₹{dest_min:,}/day vs budget ₹{group_max:,}/day"
        )

    return FactorScore(score, _budget_reason(score, dest_avg, group_max))


def _members_over(agg, daily_min) -> int:
    """Rough estimate of members who cannot afford the destination."""
    budget = agg.get('budget', {})
    if not budget:
        return 0
    # We don't have individual budgets at this level; use stddev as proxy
    return max(1, round(budget.get('stddev', 0) / daily_min))


def _budget_reason(score, dest_avg, group_max):
    if score >= 0.9:
        return f"Destination avg ₹{dest_avg:,}/day — comfortably within group budget."
    if score >= 0.7:
        return f"Affordable at mid-range spending (₹{dest_avg:,}/day avg)."
    if score >= 0.4:
        return f"Budget-friendly options available but tight for some members."
    return f"Destination cost (₹{dest_avg:,}/day) exceeds group budget ceiling."


def _score_interests(agg, dest, conflicts, highlights) -> FactorScore:
    """
    Jaccard-style overlap between destination tags and the group's popular interests.
    Popular = ≥50% of members listed that interest.
    """
    if not agg.get('interests'):
        return FactorScore(0.5, "No interest data yet.")

    popular: list[str] = agg['interests'].get('popular', [])
    dest_tags: set[str] = set(dest.tags or [])

    if not popular:
        return FactorScore(0.5, "No interests selected by enough members yet.")

    overlap = dest_tags.intersection(popular)
    score   = len(overlap) / len(popular)

    if overlap:
        highlights.append(f"Matches group interests: {', '.join(sorted(overlap))}")
    if score < 0.3:
        missing = set(popular) - dest_tags
        conflicts.append(
            f"Low interest match — destination doesn't strongly support: "
            f"{', '.join(sorted(missing)[:3])}"
        )

    reason = (
        f"{len(overlap)}/{len(popular)} popular group interests matched "
        f"({', '.join(sorted(overlap)) or 'none'})."
    )
    return FactorScore(min(score, 1.0), reason)


def _score_duration(dest, trip_duration_days, conflicts) -> FactorScore:
    """Score how well the trip length fits the destination's typical duration."""
    if trip_duration_days is None:
        return FactorScore(0.7, "No trip dates set — duration assumed compatible.")

    d_min = dest.typical_duration_days_min
    d_max = dest.typical_duration_days_max

    if d_min <= trip_duration_days <= d_max:
        return FactorScore(1.0, f"Trip duration ({trip_duration_days}d) is ideal for this destination.")
    elif trip_duration_days < d_min:
        shortfall = d_min - trip_duration_days
        score = max(0.3, 1 - shortfall / d_min)
        conflicts.append(
            f"Trip is {shortfall} day(s) shorter than recommended minimum ({d_min}d)."
        )
        return FactorScore(score, f"Trip slightly short — recommended {d_min}–{d_max} days.")
    else:
        excess = trip_duration_days - d_max
        score  = max(0.5, 1 - excess / (d_max * 2))
        return FactorScore(score, f"Trip longer than typical — may feel slow after {d_max} days.")


def _score_activity(agg, dest, conflicts, highlights) -> FactorScore:
    """Compare dominant group activity intensity with destination's best_for_intensity."""
    if not agg.get('activity_intensity'):
        return FactorScore(0.6, "No activity intensity data yet.")

    dominant  = agg['activity_intensity']['dominant']
    dest_best = dest.best_for_intensity

    compatibility = {
        ('relaxed',     'relaxed'):     1.0,
        ('relaxed',     'moderate'):    0.7,
        ('relaxed',     'adventurous'): 0.3,
        ('moderate',    'relaxed'):     0.7,
        ('moderate',    'moderate'):    1.0,
        ('moderate',    'adventurous'): 0.7,
        ('adventurous', 'relaxed'):     0.3,
        ('adventurous', 'moderate'):    0.7,
        ('adventurous', 'adventurous'): 1.0,
    }

    score = compatibility.get((dominant, dest_best), 0.5)

    if score == 1.0:
        highlights.append(f"Activity level ({dominant}) perfectly matches this destination")
    elif score < 0.5:
        conflicts.append(
            f"Activity mismatch: group prefers {dominant} pace, "
            f"but {dest.name} is best for {dest_best} travellers."
        )

    return FactorScore(
        score,
        f"Group prefers {dominant} pace; destination suits {dest_best} travellers."
    )


def _score_transport(agg, dest, conflicts) -> FactorScore:
    """Check if the group's preferred transport mode reaches the destination."""
    if not agg.get('transport'):
        return FactorScore(0.7, "No transport preference set.")

    dominant  = agg['transport']['dominant']
    reachable = dest.reachable_by or []

    if dominant == 'any' or dominant in reachable:
        return FactorScore(1.0, f"Reachable by {dominant or 'multiple modes'}.")

    # Partial credit if flight works even if they prefer something else
    if 'flight' in reachable and dominant != 'road':
        return FactorScore(0.7, f"Group prefers {dominant} but {dest.name} is mainly accessible by flight.")

    conflicts.append(
        f"Group prefers {dominant} travel, but {dest.name} is not easily reached that way "
        f"(accessible by: {', '.join(reachable)})."
    )
    return FactorScore(0.3, f"Transport mismatch — group prefers {dominant}.")


def _score_accommodation(agg, dest, conflicts) -> FactorScore:
    """Check if the destination has the group's preferred accommodation type."""
    if not agg.get('accommodation'):
        return FactorScore(0.7, "No accommodation preference set.")

    dominant  = agg['accommodation']['dominant']
    available = dest.accommodation_available or []

    if dominant in available:
        return FactorScore(1.0, f"{dominant.replace('_', ' ').title()} accommodation available.")

    conflicts.append(
        f"Group prefers {dominant} accommodation, which may be limited here."
    )
    return FactorScore(0.4, f"Preferred accommodation type ({dominant}) may not be available.")


def _seasonal_multiplier(dest, trip_month: int | None) -> float:
    """
    Return a small multiplier (0.85 – 1.0) based on whether the travel month
    is in the destination's recommended seasons.

    This is NOT a full factor — we don't want to kill off a great destination
    just because someone travels in the shoulder season. It's a nudge.
    """
    if trip_month is None:
        return 1.0
    recommended = dest.recommended_seasons or []
    if not recommended:
        return 1.0
    return 1.0 if trip_month in recommended else 0.88
