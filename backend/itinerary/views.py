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
        
        if trip.status not in ['DESTINATION_SELECTED', 'ITINERARY_GENERATED']:
            return Response({"detail": "Destination not finalized."}, status=status.HTTP_400_BAD_REQUEST)

        # Update status to indicate processing
        trip.status = 'GENERATING_ITINERARY'
        trip.save(update_fields=['status'])

        # Trigger background task
        from .tasks import generate_itinerary_task
        generate_itinerary_task.delay(trip.id)
        
        return Response({"detail": "Itinerary generation started."}, status=status.HTTP_202_ACCEPTED)
