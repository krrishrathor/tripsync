from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from trips.models import Trip
from trips.permissions import IsTripMemberOrOwner, IsTripOwner
from .models import Itinerary
from .serializers import ItinerarySerializer
from .services import generate_itinerary_for_trip

class ItineraryView(APIView):
    permission_classes = [IsTripMemberOrOwner]

    def get(self, request, trip_id):
        itinerary = get_object_or_404(Itinerary, trip_id=trip_id)
        self.check_object_permissions(request, itinerary.trip)
        serializer = ItinerarySerializer(itinerary)
        return Response(serializer.data)

class GenerateItineraryView(APIView):
    permission_classes = [IsTripOwner]

    def post(self, request, trip_id):
        trip = get_object_or_404(Trip, pk=trip_id)
        self.check_object_permissions(request, trip)
        try:
            itinerary = generate_itinerary_for_trip(trip)
            serializer = ItinerarySerializer(itinerary)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
