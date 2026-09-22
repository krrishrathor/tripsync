"""
Tests for preference submission, validation, and aggregation.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from trips.models import Trip, TripMember
from trip_preferences.models import MemberPreference
from trip_preferences.aggregation import aggregate

User = get_user_model()


def create_user(username, email):
    return User.objects.create_user(username=username, email=email, password='Pass1234!')


def create_trip_with_owner(owner, name='Test Trip'):
    trip = Trip.objects.create(name=name, owner=owner)
    TripMember.objects.create(trip=trip, user=owner, role='OWNER')
    return trip


class PreferenceSubmissionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user('owner', 'owner@test.com')
        self.trip = create_trip_with_owner(self.user)
        self.client.force_authenticate(user=self.user)
        self.url = f'/api/trips/{self.trip.id}/preferences/me/'

    def test_create_preference(self):
        data = {
            'min_budget': '5000.00',
            'max_budget': '15000.00',
            'travel_style': 'mid_range',
            'interests': ['beaches', 'food'],
            'diet_type': 'vegetarian',
            'activity_intensity': 'moderate',
        }
        response = self.client.put(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(MemberPreference.objects.count(), 1)

    def test_update_preference_is_idempotent(self):
        """PUT twice should update, not create a second record."""
        data = {'min_budget': '5000.00', 'max_budget': '15000.00', 'travel_style': 'mid_range',
                'interests': ['beaches'], 'diet_type': 'vegetarian', 'activity_intensity': 'moderate'}
        self.client.put(self.url, data, format='json')
        data['max_budget'] = '20000.00'
        self.client.put(self.url, data, format='json')
        self.assertEqual(MemberPreference.objects.count(), 1)
        self.assertEqual(float(MemberPreference.objects.first().max_budget), 20000.0)

    def test_invalid_interest_rejected(self):
        data = {'interests': ['beaches', 'alien_abduction'], 'diet_type': 'vegetarian',
                'travel_style': 'mid_range', 'activity_intensity': 'moderate'}
        response = self.client.put(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_budget_order_validation(self):
        data = {'min_budget': '20000.00', 'max_budget': '5000.00',
                'travel_style': 'mid_range', 'interests': [], 'diet_type': 'non_vegetarian',
                'activity_intensity': 'moderate'}
        response = self.client.put(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_member_cannot_submit(self):
        outsider = create_user('outsider', 'out@test.com')
        self.client.force_authenticate(user=outsider)
        response = self.client.put(self.url, {'travel_style': 'luxury',
                                               'interests': [], 'diet_type': 'non_vegetarian',
                                               'activity_intensity': 'relaxed'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AggregationTests(TestCase):
    def setUp(self):
        self.owner = create_user('owner', 'owner@agg.com')
        self.member2 = create_user('member2', 'm2@agg.com')
        self.member3 = create_user('member3', 'm3@agg.com')
        self.trip = create_trip_with_owner(self.owner)
        TripMember.objects.create(trip=self.trip, user=self.member2, role='MEMBER')
        TripMember.objects.create(trip=self.trip, user=self.member3, role='MEMBER')

    def _pref(self, user, **kwargs):
        defaults = dict(
            min_budget=5000, max_budget=15000,
            travel_style='mid_range', preferred_transport='any',
            interests=['beaches', 'food'], diet_type='non_vegetarian',
            accommodation_type='mid_range', activity_intensity='moderate',
        )
        defaults.update(kwargs)
        MemberPreference.objects.create(trip=self.trip, user=user, **defaults)

    def test_aggregate_returns_correct_member_count(self):
        self._pref(self.owner)
        result = aggregate(self.trip.id)
        self.assertEqual(result['member_count'], 3)
        self.assertEqual(result['preferences_submitted'], 1)
        self.assertAlmostEqual(result['completion_pct'], 33.3, places=0)

    def test_aggregate_detects_diet_conflict(self):
        self._pref(self.owner, diet_type='vegetarian')
        self._pref(self.member2, diet_type='non_vegetarian')
        self._pref(self.member3, diet_type='non_vegetarian')
        result = aggregate(self.trip.id)
        conflict_types = [c['type'] for c in result['conflicts']]
        self.assertIn('diet', conflict_types)

    def test_aggregate_interest_ranking(self):
        self._pref(self.owner, interests=['beaches', 'food'])
        self._pref(self.member2, interests=['beaches', 'mountains'])
        self._pref(self.member3, interests=['food', 'culture'])
        result = aggregate(self.trip.id)
        ranked = result['interests']['all_ranked']
        top = ranked[0]['interest']
        # beaches and food both appear 2 times; top should be one of them
        self.assertIn(top, {'beaches', 'food'})
        self.assertIn('beaches', result['interests']['popular'])

    def test_empty_preferences_returns_safe_defaults(self):
        result = aggregate(self.trip.id)
        self.assertEqual(result['preferences_submitted'], 0)
        self.assertIsNone(result['budget'])
        self.assertEqual(result['conflicts'], [])
