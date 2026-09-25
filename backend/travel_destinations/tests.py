"""
Tests for the scoring engine and the compatible-destinations API endpoint.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from trips.models import Trip, TripMember
from trip_preferences.models import MemberPreference
from travel_destinations.models import Destination
from travel_destinations.scoring import score_destinations

User = get_user_model()


def _make_dest(**overrides):
    defaults = dict(
        name="Test Beach", country="India", region="Test",
        description="Test", estimated_daily_cost_min=2000,
        estimated_daily_cost_max=6000,
        tags=["beaches", "food"], popular_activities=["Swimming"],
        best_for_intensity="moderate", travel_difficulty="easy",
        recommended_seasons=[11, 12, 1], typical_duration_days_min=3,
        typical_duration_days_max=7,
        approximate_travel_hours_from_metro=2,
        reachable_by=["flight", "train"],
        accommodation_available=["budget", "mid_range", "luxury"],
    )
    defaults.update(overrides)
    return Destination.objects.create(**defaults)


def _agg(**overrides):
    base = {
        "member_count": 3,
        "preferences_submitted": 3,
        "completion_pct": 100.0,
        "budget": {
            "median_max_budget": 15000,
            "lowest_max_budget": 10000,
            "highest_max_budget": 20000,
            "group_min_acceptable": 10000,
            "stddev": 3000,
            "members_with_budget": 3,
        },
        "interests": {
            "all_ranked": [{"interest": "beaches", "count": 3, "pct": 100},
                           {"interest": "food", "count": 2, "pct": 67}],
            "popular": ["beaches", "food"],
            "common": ["beaches"],
        },
        "travel_style": {"dominant": "mid_range", "distribution": {"mid_range": 3}},
        "transport": {"dominant": "flight", "distribution": {"flight": 3}},
        "accommodation": {"dominant": "mid_range", "distribution": {"mid_range": 3}},
        "activity_intensity": {"dominant": "moderate", "distribution": {"moderate": 3}},
        "diet": {"distribution": {"non_vegetarian": 3}, "most_restrictive": "non_vegetarian", "allergies": []},
        "conflicts": [],
    }
    base.update(overrides)
    return base


class ScoringEngineTests(TestCase):

    def test_perfect_match_scores_high(self):
        dest = _make_dest(
            tags=["beaches", "food"],
            best_for_intensity="moderate",
            reachable_by=["flight"],
            accommodation_available=["budget", "mid_range", "luxury"],
            estimated_daily_cost_min=1500,
            estimated_daily_cost_max=5000,
        )
        scores = score_destinations(_agg(), [dest])
        self.assertEqual(len(scores), 1)
        self.assertGreater(scores[0].overall, 75)

    def test_over_budget_destination_scores_lower(self):
        expensive = _make_dest(
            name="Luxury Resort", region="Test2",
            estimated_daily_cost_min=15000,
            estimated_daily_cost_max=30000,
            tags=["beaches"],
        )
        affordable = _make_dest(
            name="Budget Beach", region="Test3",
            estimated_daily_cost_min=1000,
            estimated_daily_cost_max=3000,
            tags=["beaches"],
        )
        agg = _agg()
        agg['budget']['group_min_acceptable'] = 5000

        scores = score_destinations(agg, [expensive, affordable])
        expensive_score = next(s for s in scores if s.destination_name == "Luxury Resort")
        affordable_score = next(s for s in scores if s.destination_name == "Budget Beach")

        self.assertGreater(affordable_score.overall, expensive_score.overall)
        # Expensive should generate a budget conflict
        self.assertTrue(any('budget' in c.lower() or 'over budget' in c.lower() or 'exceed' in c.lower()
                            for c in expensive_score.conflicts), msg=f"Expected conflict, got: {expensive_score.conflicts}")

    def test_interest_mismatch_lowers_score(self):
        dest_match = _make_dest(name="Match Dest", region="R1", tags=["beaches", "food"])
        dest_mismatch = _make_dest(name="Mismatch Dest", region="R2", tags=["sports", "shopping"])

        agg = _agg()
        agg['interests']['popular'] = ['beaches', 'food']

        scores = score_destinations(agg, [dest_match, dest_mismatch])
        m = next(s for s in scores if s.destination_name == "Match Dest")
        mm = next(s for s in scores if s.destination_name == "Mismatch Dest")
        self.assertGreater(m.interest.score, mm.interest.score)

    def test_activity_intensity_mismatch_detected(self):
        dest = _make_dest(best_for_intensity="adventurous")
        agg = _agg()
        agg['activity_intensity']['dominant'] = 'relaxed'

        scores = score_destinations(agg, [dest])
        self.assertLess(scores[0].activity.score, 0.5)

    def test_no_preferences_returns_neutral_scores(self):
        dest = _make_dest()
        agg = {
            "member_count": 3, "preferences_submitted": 0, "completion_pct": 0,
            "budget": None, "interests": None, "travel_style": None,
            "transport": None, "accommodation": None, "activity_intensity": None,
            "diet": None, "conflicts": [],
        }
        scores = score_destinations(agg, [dest])
        # Should return a result, not crash
        self.assertEqual(len(scores), 1)
        self.assertGreater(scores[0].overall, 0)

    def test_seasonal_penalty_applied(self):
        """Destination recommended in summer should score less if travelling in winter."""
        from datetime import date
        dest_summer = _make_dest(name="Summer Only", region="S1", recommended_seasons=[5, 6, 7, 8])
        dest_allsea  = _make_dest(name="All Season",  region="S2", recommended_seasons=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
        scores = score_destinations(
            _agg(), [dest_summer, dest_allsea],
            trip_start_date=date(2026, 12, 1),
        )
        summer_s = next(s for s in scores if s.destination_name == "Summer Only")
        all_s    = next(s for s in scores if s.destination_name == "All Season")
        self.assertLess(summer_s.overall, all_s.overall)


class CompatibleDestinationsAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(username='owner', email='owner@test.com', password='Pass123!')
        self.trip  = Trip.objects.create(name='Test Trip', owner=self.owner)
        TripMember.objects.create(trip=self.trip, user=self.owner, role='OWNER')
        self.client.force_authenticate(user=self.owner)
        # Seed at least one destination
        _make_dest()

    def test_returns_scored_list(self):
        url = f'/api/trips/{self.trip.id}/compatible-destinations/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertIn('overall', response.data[0])

    def test_non_member_gets_403(self):
        outsider = User.objects.create_user(username='out', email='out@test.com', password='Pass123!')
        self.client.force_authenticate(user=outsider)
        url = f'/api/trips/{self.trip.id}/compatible-destinations/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
