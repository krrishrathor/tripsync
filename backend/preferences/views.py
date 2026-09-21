from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Preference
from .serializers import PreferenceSerializer
from .services import PreferenceAggregationService
from trips.models import Trip
from trips.permissions import IsTripMemberOrOwner

class UserPreferenceView(APIView):
    """View to get or update the current user's preferences for a specific trip"""
    permission_classes = [permissions.IsAuthenticated, IsTripMemberOrOwner]
    
    def get(self, request, trip_id):
        trip = get_object_or_404(Trip, id=trip_id)
        self.check_object_permissions(request, trip)
        
        try:
            preference = Preference.objects.get(user=request.user, trip=trip)
            serializer = PreferenceSerializer(preference)
            return Response(serializer.data)
        except Preference.DoesNotExist:
            return Response({"detail": "Preferences not found."}, status=status.HTTP_404_NOT_FOUND)
            
    def post(self, request, trip_id):
        trip = get_object_or_404(Trip, id=trip_id)
        self.check_object_permissions(request, trip)
        
        # Check if exists to update, else create
        preference, created = Preference.objects.get_or_create(
            user=request.user, 
            trip=trip,
            defaults={'min_budget': 0, 'max_budget': 0}
        )
        
        serializer = PreferenceSerializer(preference, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GroupPreferenceView(APIView):
    """View to get the aggregated preferences for a trip"""
    permission_classes = [permissions.IsAuthenticated, IsTripMemberOrOwner]
    
    def get(self, request, trip_id):
        trip = get_object_or_404(Trip, id=trip_id)
        self.check_object_permissions(request, trip)
        
        aggregated_data = PreferenceAggregationService.aggregate_trip_preferences(trip.id)
        return Response(aggregated_data)
