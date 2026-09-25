"""
Tests for voting: cast, change, retract, summary, destination selection,
race conditions, and permission checks.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from trips.models import Trip, TripMember
from travel_destinations.models import Destination
from voting.models import Vote
from voting.services import cast_or_change_vote, remove_vote, get_vote_summary, select_destination

User = get_user_model()


# ── helpers ──────────────────────────────────────────────────────────────────

def make_user(username, email):
    return User.objects.create_user(username=username, email=email, password='Pass1234!')

def make_trip(owner, name='Test Trip'):
    trip = Trip.objects.create(name=name, owner=owner)
    TripMember.objects.create(trip=trip, user=owner, role='OWNER')
    return trip

def make_dest(name='Goa', region='Goa'):
    return Destination.objects.create(
        name=name, country='India', region=region, description='Test',
        estimated_daily_cost_min=2000, estimated_daily_cost_max=6000,
        tags=['beaches'], popular_activities=['Swimming'],
        best_for_intensity='moderate', travel_difficulty='easy',
        reachable_by=['flight'], accommodation_available=['mid_range'],
    )


# ── Service layer tests ───────────────────────────────────────────────────────

class VotingServiceTests(TestCase):
    def setUp(self):
        self.owner = make_user('owner', 'owner@v.com')
        self.member = make_user('member', 'member@v.com')
        self.trip = make_trip(self.owner)
        TripMember.objects.create(trip=self.trip, user=self.member, role='MEMBER')
        self.goa = make_dest('Goa', 'Goa')
        self.manali = make_dest('Manali', 'HP')

    def test_cast_vote(self):
        vote = cast_or_change_vote(self.trip, self.owner, self.goa.id)
        self.assertEqual(vote.destination, self.goa)
        self.assertEqual(Vote.objects.count(), 1)

    def test_change_vote_is_idempotent(self):
        """Voting twice should update the existing record, not create a second."""
        cast_or_change_vote(self.trip, self.owner, self.goa.id)
        cast_or_change_vote(self.trip, self.owner, self.manali.id)
        self.assertEqual(Vote.objects.count(), 1)
        self.assertEqual(Vote.objects.first().destination, self.manali)

    def test_two_members_can_vote_differently(self):
        cast_or_change_vote(self.trip, self.owner, self.goa.id)
        cast_or_change_vote(self.trip, self.member, self.manali.id)
        self.assertEqual(Vote.objects.count(), 2)

    def test_remove_vote(self):
        cast_or_change_vote(self.trip, self.owner, self.goa.id)
        removed = remove_vote(self.trip, self.owner)
        self.assertTrue(removed)
        self.assertEqual(Vote.objects.count(), 0)

    def test_remove_nonexistent_vote_returns_false(self):
        self.assertFalse(remove_vote(self.trip, self.owner))

    def test_vote_summary_tallies_correctly(self):
        cast_or_change_vote(self.trip, self.owner, self.goa.id)
        cast_or_change_vote(self.trip, self.member, self.goa.id)
        summary = get_vote_summary(self.trip, self.owner)
        self.assertEqual(summary['total_voters'], 2)
        self.assertEqual(summary['results'][0]['vote_count'], 2)
        self.assertEqual(summary['results'][0]['destination'], self.goa)

    def test_vote_summary_my_vote_correct(self):
        cast_or_change_vote(self.trip, self.owner, self.goa.id)
        cast_or_change_vote(self.trip, self.member, self.manali.id)
        summary = get_vote_summary(self.trip, self.owner)
        self.assertEqual(summary['my_vote']['destination_id'], self.goa.id)

    def test_select_destination_updates_status(self):
        trip = select_destination(self.trip, self.owner, self.goa.id)
        self.assertEqual(trip.status, 'DESTINATION_SELECTED')
        self.assertEqual(trip.selected_destination, self.goa)

    def test_non_owner_cannot_select_destination(self):
        with self.assertRaises(PermissionError):
            select_destination(self.trip, self.member, self.goa.id)

    def test_select_destination_when_not_planning_raises(self):
        select_destination(self.trip, self.owner, self.goa.id)
        with self.assertRaises(ValueError):
            select_destination(self.trip, self.owner, self.manali.id)


# ── API tests ─────────────────────────────────────────────────────────────────

class VotingAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner  = make_user('owner2', 'o2@v.com')
        self.member = make_user('member2', 'm2@v.com')
        self.trip   = make_trip(self.owner)
        TripMember.objects.create(trip=self.trip, user=self.member, role='MEMBER')
        self.goa    = make_dest('Goa2', 'Goa2')
        self.client.force_authenticate(user=self.owner)

    def _vote_url(self):
        return f'/api/trips/{self.trip.id}/votes/'

    def _select_url(self):
        return f'/api/trips/{self.trip.id}/select-destination/'

    def test_cast_vote_api(self):
        response = self.client.post(self._vote_url(), {'destination_id': self.goa.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Vote.objects.count(), 1)

    def test_get_vote_summary_api(self):
        cast_or_change_vote(self.trip, self.owner, self.goa.id)
        response = self.client.get(self._vote_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_voters'], 1)
        self.assertEqual(len(response.data['results']), 1)

    def test_retract_vote_api(self):
        cast_or_change_vote(self.trip, self.owner, self.goa.id)
        response = self.client.delete(self._vote_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Vote.objects.count(), 0)

    def test_non_member_cannot_vote(self):
        outsider = make_user('out3', 'out3@v.com')
        self.client.force_authenticate(user=outsider)
        response = self.client.post(self._vote_url(), {'destination_id': self.goa.id})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_select_destination(self):
        response = self.client.post(self._select_url(), {'destination_id': self.goa.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['trip_status'], 'DESTINATION_SELECTED')

    def test_member_cannot_select_destination(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.post(self._select_url(), {'destination_id': self.goa.id})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_voting_closed_after_destination_selected(self):
        select_destination(self.trip, self.owner, self.goa.id)
        response = self.client.post(self._vote_url(), {'destination_id': self.goa.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
