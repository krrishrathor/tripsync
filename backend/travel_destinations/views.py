from dataclasses import asdict
from datetime import date

from django.core.cache import cache
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from trips.models import Trip, TripMember
from trip_preferences.aggregation import aggregate
from .models import Destination
from .scoring import score_destinations
from .serializers import DestinationSerializer, ScoredDestinationSerializer

CACHE_TTL = 60 * 10  # 10 minutes — scoring is cheap, but avoid recomputing on every render


class DestinationListView(generics.ListAPIView):
    """
    GET /api/destinations/
    Returns all active destinations (no scoring).
    Used for browsing / admin.
    """
    queryset = Destination.objects.filter(is_active=True)
    serializer_class = DestinationSerializer
    permission_classes = [permissions.IsAuthenticated]


class TripCompatibleDestinationsView(APIView):
    """
    GET /api/trips/<trip_id>/compatible-destinations/

    Returns all destinations scored and ranked against the group's aggregated
    preferences. Results are cached for 10 minutes per trip.

    Query params:
        refresh=1  — bypass cache (useful after a member updates preferences)
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, trip_id):
        trip = get_object_or_404(Trip, pk=trip_id)

        if not TripMember.objects.filter(trip=trip, user=request.user).exists():
            return Response(
                {"detail": "You are not a member of this trip."},
                status=status.HTTP_403_FORBIDDEN,
            )

        cache_key = f"trip_compat_{trip_id}"
        refresh   = request.query_params.get('refresh', '0') == '1'

        if not refresh:
            cached = cache.get(cache_key)
            if cached:
                return Response(cached)

        # ── Aggregate preferences ─────────────────────────────────────────────
        agg = aggregate(trip_id)

        # ── Parse trip dates ──────────────────────────────────────────────────
        start = trip.start_date if trip.start_date else None
        end   = trip.end_date   if trip.end_date   else None

        # ── Score all destinations ────────────────────────────────────────────
        destinations = Destination.objects.filter(is_active=True)
        scores = score_destinations(agg, list(destinations), start, end)

        # ── Serialise ─────────────────────────────────────────────────────────
        dest_map = {d.id: d for d in destinations}

        payload = []
        for score in scores:
            dest_obj = dest_map.get(score.destination_id)
            if not dest_obj:
                continue
            payload.append({
                "destination": DestinationSerializer(dest_obj).data,
                "overall":     score.overall,
                "budget":      {"score": round(score.budget.score * 100), "reason": score.budget.reason},
                "interest":    {"score": round(score.interest.score * 100), "reason": score.interest.reason},
                "duration":    {"score": round(score.duration.score * 100), "reason": score.duration.reason},
                "activity":    {"score": round(score.activity.score * 100), "reason": score.activity.reason},
                "transport":   {"score": round(score.transport.score * 100), "reason": score.transport.reason},
                "accommodation": {"score": round(score.accommodation.score * 100), "reason": score.accommodation.reason},
                "conflicts":   score.conflicts,
                "highlights":  score.highlights,
            })

        cache.set(cache_key, payload, CACHE_TTL)
        return Response(payload)
