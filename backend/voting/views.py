from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.core.cache import cache

from trips.models import Trip, TripMember
from travel_destinations.serializers import DestinationSerializer
from .services import cast_or_change_vote, remove_vote, get_vote_summary, select_destination
from .serializers import VoteSerializer


class VoteView(APIView):
    """
    GET    /api/trips/<trip_id>/votes/              — full vote summary for the trip
    POST   /api/trips/<trip_id>/votes/              — cast or change my vote
    DELETE /api/trips/<trip_id>/votes/              — retract my vote
    """
    permission_classes = [IsAuthenticated]

    def _get_trip_or_403(self, request, trip_id):
        trip = get_object_or_404(Trip, pk=trip_id)
        if not TripMember.objects.filter(trip=trip, user=request.user).exists():
            return None, Response(
                {"detail": "You are not a member of this trip."},
                status=status.HTTP_403_FORBIDDEN
            )
        return trip, None

    def get(self, request, trip_id):
        trip, err = self._get_trip_or_403(request, trip_id)
        if err:
            return err

        summary = get_vote_summary(trip, request.user)

        # Serialize destinations inline
        serialized_results = []
        for r in summary['results']:
            serialized_results.append({
                'destination':        DestinationSerializer(r['destination']).data,
                'vote_count':         r['vote_count'],
                'vote_pct':           r['vote_pct'],
                'voters':             r['voters'],
                'current_user_voted': r['current_user_voted'],
            })

        return Response({
            'total_voters':      summary['total_voters'],
            'member_count':      summary['member_count'],
            'participation_pct': summary['participation_pct'],
            'my_vote':           summary['my_vote'],
            'results':           serialized_results,
        })

    def post(self, request, trip_id):
        trip, err = self._get_trip_or_403(request, trip_id)
        if err:
            return err

        if trip.status != 'PLANNING':
            return Response(
                {"detail": "Voting is closed — the destination has already been selected."},
                status=status.HTTP_400_BAD_REQUEST
            )

        destination_id = request.data.get('destination_id')
        if not destination_id:
            return Response(
                {"detail": "destination_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            vote = cast_or_change_vote(trip, request.user, int(destination_id))
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Invalidate compatible-destinations cache so scores refresh
        cache.delete(f"trip_compat_{trip_id}")

        return Response({
            "detail": "Vote recorded.",
            "destination_id":   vote.destination_id,
            "destination_name": vote.destination.name,
        }, status=status.HTTP_200_OK)

    def delete(self, request, trip_id):
        trip, err = self._get_trip_or_403(request, trip_id)
        if err:
            return err

        if trip.status != 'PLANNING':
            return Response(
                {"detail": "Voting is closed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        removed = remove_vote(trip, request.user)
        if removed:
            return Response({"detail": "Vote removed."}, status=status.HTTP_200_OK)
        return Response({"detail": "No vote to remove."}, status=status.HTTP_404_NOT_FOUND)


class SelectDestinationView(APIView):
    """
    POST /api/trips/<trip_id>/select-destination/
    Body: { "destination_id": <int> }

    Only the trip OWNER can call this. Locks voting and sets trip status
    to DESTINATION_SELECTED.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, trip_id):
        trip = get_object_or_404(Trip, pk=trip_id)

        destination_id = request.data.get('destination_id')
        if not destination_id:
            return Response(
                {"detail": "destination_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            updated_trip = select_destination(trip, request.user, int(destination_id))
        except PermissionError as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "detail": "Destination selected. Voting is now closed.",
            "trip_status":        updated_trip.status,
            "destination_id":     updated_trip.selected_destination_id,
            "destination_name":   updated_trip.selected_destination.name,
        }, status=status.HTTP_200_OK)
