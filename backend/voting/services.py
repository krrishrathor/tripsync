"""
Voting service layer.

Keeping business logic here (not in views) so it can be reused by:
- REST views (Phase 6)
- WebSocket consumers (Phase 7)
- Tests
"""
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404

from trips.models import Trip, TripMember
from travel_destinations.models import Destination
from .models import Vote


def cast_or_change_vote(trip: Trip, user, destination_id: int) -> Vote:
    """
    Upsert a vote. If the user already voted in this trip, update to the new
    destination. Returns the (possibly updated) Vote instance.

    Uses select_for_update inside a transaction to prevent race conditions
    when two requests arrive simultaneously for the same user+trip.
    """
    # Verify destination is active
    destination = get_object_or_404(Destination, pk=destination_id, is_active=True)

    with transaction.atomic():
        vote, created = Vote.objects.select_for_update().get_or_create(
            trip=trip,
            user=user,
            defaults={'destination': destination},
        )
        if not created and vote.destination_id != destination_id:
            vote.destination = destination
            vote.save(update_fields=['destination', 'updated_at'])

    return vote


def remove_vote(trip: Trip, user) -> bool:
    """Remove the user's vote. Returns True if a vote existed."""
    deleted, _ = Vote.objects.filter(trip=trip, user=user).delete()
    return deleted > 0


def get_vote_summary(trip: Trip, requesting_user) -> dict:
    """
    Return a structured vote summary for all destinations that have at least
    one vote, plus the requesting user's current vote.

    Example return value:
    {
        "total_voters": 3,
        "member_count": 5,
        "participation_pct": 60.0,
        "my_vote": {"destination_id": 1, "destination_name": "Goa"},
        "results": [
            {
                "destination": <Destination obj>,
                "vote_count": 2,
                "vote_pct": 66.7,
                "voters": [{"username": "alice"}, {"username": "bob"}],
                "current_user_voted": True,
            },
            ...
        ]
    }
    """
    total_members = TripMember.objects.filter(trip=trip).count()
    all_votes     = (
        Vote.objects.filter(trip=trip)
        .select_related('destination', 'user')
        .order_by('destination__name')
    )
    total_voters = all_votes.values('user').distinct().count()

    # Group by destination
    dest_map: dict[int, dict] = {}
    for vote in all_votes:
        did = vote.destination_id
        if did not in dest_map:
            dest_map[did] = {
                'destination': vote.destination,
                'vote_count': 0,
                'voters': [],
                'current_user_voted': False,
            }
        dest_map[did]['vote_count'] += 1
        dest_map[did]['voters'].append({
            'username':   vote.user.username,
            'first_name': vote.user.first_name,
            'last_name':  vote.user.last_name,
        })
        if vote.user_id == requesting_user.id:
            dest_map[did]['current_user_voted'] = True

    # Sort by vote count descending
    results = sorted(dest_map.values(), key=lambda d: d['vote_count'], reverse=True)
    for r in results:
        r['vote_pct'] = round(r['vote_count'] / total_members * 100, 1) if total_members else 0

    # My vote
    my_vote_obj = Vote.objects.filter(trip=trip, user=requesting_user).select_related('destination').first()
    my_vote = {
        'destination_id':   my_vote_obj.destination_id   if my_vote_obj else None,
        'destination_name': my_vote_obj.destination.name if my_vote_obj else None,
    }

    return {
        'total_voters':       total_voters,
        'member_count':       total_members,
        'participation_pct':  round(total_voters / total_members * 100, 1) if total_members else 0,
        'my_vote':            my_vote,
        'results':            results,
    }


def select_destination(trip: Trip, owner, destination_id: int) -> Trip:
    """
    Owner finalises the group decision. Updates trip status to DESTINATION_SELECTED.
    Only callable by the trip owner.

    Raises PermissionError if caller is not owner.
    Raises ValueError if trip is not in PLANNING status.
    """
    if trip.owner_id != owner.id:
        raise PermissionError("Only the trip owner can select the final destination.")

    if trip.status != 'PLANNING':
        raise ValueError(f"Cannot select destination when trip status is '{trip.status}'.")

    destination = get_object_or_404(Destination, pk=destination_id, is_active=True)

    with transaction.atomic():
        trip.status = 'DESTINATION_SELECTED'
        # Store destination FK — add selected_destination FK to Trip model
        trip.selected_destination = destination
        trip.save(update_fields=['status', 'selected_destination', 'updated_at'])

    return trip
