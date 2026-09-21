from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from .models import Trip, TripMember

User = get_user_model()

class TripTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(username='owner', email='owner@example.com', password='password123')
        self.user2 = User.objects.create_user(username='member', email='member@example.com', password='password123')
        
        # Authenticate user1
        self.client.force_authenticate(user=self.user1)

    def test_create_trip(self):
        url = reverse('trip-list-create')
        data = {
            'name': 'Goa 2026',
            'description': 'Fun trip',
            'total_budget': '50000.00'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Trip.objects.count(), 1)
        self.assertEqual(TripMember.objects.count(), 1)
        
        trip = Trip.objects.first()
        self.assertEqual(trip.owner, self.user1)
        
        member = TripMember.objects.first()
        self.assertEqual(member.user, self.user1)
        self.assertEqual(member.role, 'OWNER')

    def test_join_trip(self):
        # User 1 creates trip
        trip = Trip.objects.create(name='Test Trip', owner=self.user1)
        TripMember.objects.create(trip=trip, user=self.user1, role='OWNER')
        
        # User 2 joins
        self.client.force_authenticate(user=self.user2)
        url = reverse('trip-join', kwargs={'invite_code': trip.invite_code})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(TripMember.objects.count(), 2)
        
        # Try joining again
        response2 = self.client.post(url)
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
