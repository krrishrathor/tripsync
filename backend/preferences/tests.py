from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from trips.models import Trip, TripMember
from .models import Preference
from .services import PreferenceAggregationService

User = get_user_model()

class PreferenceTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(username='user1', email='user1@example.com', password='password123')
        self.user2 = User.objects.create_user(username='user2', email='user2@example.com', password='password123')
        
        self.trip = Trip.objects.create(name='Bali 2026', owner=self.user1)
        TripMember.objects.create(trip=self.trip, user=self.user1, role='OWNER')
        TripMember.objects.create(trip=self.trip, user=self.user2, role='MEMBER')
        
        self.client.force_authenticate(user=self.user1)
        self.my_prefs_url = reverse('my-preferences', kwargs={'trip_id': self.trip.id})
        self.group_prefs_url = reverse('group-preferences', kwargs={'trip_id': self.trip.id})

    def test_submit_preference(self):
        data = {
            'max_budget': 50000.00,
            'interests': ['beaches', 'food'],
            'travel_style': 'relaxed'
        }
        response = self.client.post(self.my_prefs_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Preference.objects.count(), 1)
        
        # Test update
        data['max_budget'] = 60000.00
        response = self.client.post(self.my_prefs_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Preference.objects.get(user=self.user1).max_budget, 60000.00)

    def test_preference_aggregation(self):
        Preference.objects.create(
            user=self.user1, trip=self.trip, max_budget=40000, 
            interests=['beaches', 'culture'], travel_style='relaxed', food_preferences=['vegan']
        )
        Preference.objects.create(
            user=self.user2, trip=self.trip, max_budget=80000, 
            interests=['beaches', 'adventure'], travel_style='packed', food_preferences=['non-vegetarian']
        )
        
        response = self.client.get(self.group_prefs_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertEqual(data['budget']['min_acceptable'], 40000)
        self.assertIn('beaches', data['interests']['common'])
        self.assertIn('vegan', data['food_requirements'])
        self.assertTrue(len(data['conflicts']) > 0) # Should detect budget variance and style conflict
