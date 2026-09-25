from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from trips.models import Trip, TripMember
from travel_destinations.models import Destination
from trip_preferences.models import MemberPreference
from itinerary.models import Itinerary, DailyPlan, Activity
from itinerary.services import generate_itinerary_for_trip

User = get_user_model()

class ItineraryTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', email='o@a.com', password='pw')
        self.member = User.objects.create_user(username='member', email='m@a.com', password='pw')
        
        self.dest = Destination.objects.create(
            name='Paris', country='France', region='Ile-de-France',
            estimated_daily_cost_min=100, estimated_daily_cost_max=300
        )
        
        self.trip = Trip.objects.create(
            name='Euro Trip', owner=self.owner, status='DESTINATION_SELECTED',
            selected_destination=self.dest
        )
        TripMember.objects.create(trip=self.trip, user=self.owner, role='OWNER')
        TripMember.objects.create(trip=self.trip, user=self.member, role='MEMBER')
        
        MemberPreference.objects.create(
            trip=self.trip, user=self.owner, max_budget=200.00, interests=['Art', 'Food']
        )
        
        self.client = APIClient()

    def test_generate_itinerary_service(self):
        # We test the mock fallback since OPENAI_API_KEY isn't set in tests
        itinerary = generate_itinerary_for_trip(self.trip)
        
        self.assertEqual(itinerary.trip, self.trip)
        self.assertEqual(self.trip.status, 'ITINERARY_GENERATED')
        
        # Default duration is 3 days
        self.assertEqual(itinerary.days.count(), 3)
        
        day1 = itinerary.days.first()
        self.assertEqual(day1.day_number, 1)
        self.assertEqual(day1.activities.count(), 3)
        # Sorted alphabetically by time_of_day by default
        self.assertEqual(day1.activities.first().time_of_day, 'Afternoon')

    def test_generate_itinerary_api(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(f'/api/trips/{self.trip.id}/itinerary/generate/')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('days', response.data)
        self.assertEqual(len(response.data['days']), 3)

    def test_member_cannot_generate_itinerary(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.post(f'/api/trips/{self.trip.id}/itinerary/generate/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_get_itinerary(self):
        # Generate first
        generate_itinerary_for_trip(self.trip)
        
        self.client.force_authenticate(user=self.member)
        response = self.client.get(f'/api/trips/{self.trip.id}/itinerary/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['days']), 3)

    def test_cannot_generate_if_not_destination_selected(self):
        self.trip.status = 'PLANNING'
        self.trip.save()
        
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(f'/api/trips/{self.trip.id}/itinerary/generate/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
