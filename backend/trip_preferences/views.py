from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from trips.models import Trip, TripMember
from .models import MemberPreference
from .serializers import MemberPreferenceSerializer
from .aggregation import aggregate


class MyPreferenceView(APIView):
    """
    GET  /api/trips/<trip_id>/preferences/me/   → retrieve my preference for this trip
    PUT  /api/trips/<trip_id>/preferences/me/   → create or update my preference
    """
    permission_classes = [IsAuthenticated]

    def _get_trip_and_check_membership(self, request, trip_id):
        trip = get_object_or_404(Trip, pk=trip_id)
        if not TripMember.objects.filter(trip=trip, user=request.user).exists():
            return None, Response(
                {"detail": "You are not a member of this trip."},
                status=status.HTTP_403_FORBIDDEN
            )
        return trip, None

    def get(self, request, trip_id):
        trip, err = self._get_trip_and_check_membership(request, trip_id)
        if err:
            return err

        try:
            pref = MemberPreference.objects.get(trip=trip, user=request.user)
            return Response(MemberPreferenceSerializer(pref).data)
        except MemberPreference.DoesNotExist:
            return Response({}, status=status.HTTP_204_NO_CONTENT)

    def put(self, request, trip_id):
        trip, err = self._get_trip_and_check_membership(request, trip_id)
        if err:
            return err

        # Check that trip is still in PLANNING state – preferences locked after destination selected
        if trip.status != 'PLANNING':
            return Response(
                {"detail": "Preferences cannot be changed after destination has been selected."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            pref = MemberPreference.objects.get(trip=trip, user=request.user)
            serializer = MemberPreferenceSerializer(pref, data=request.data, partial=True)
        except MemberPreference.DoesNotExist:
            serializer = MemberPreferenceSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save(trip=trip, user=request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GroupPreferenceAggregateView(APIView):
    """
    GET /api/trips/<trip_id>/preferences/aggregate/

    Returns the deterministically aggregated group preferences.
    No LLM involved – pure Python arithmetic and Counter logic.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, trip_id):
        trip = get_object_or_404(Trip, pk=trip_id)

        if not TripMember.objects.filter(trip=trip, user=request.user).exists():
            return Response(
                {"detail": "You are not a member of this trip."},
                status=status.HTTP_403_FORBIDDEN
            )

        result = aggregate(trip_id)
        return Response(result)
