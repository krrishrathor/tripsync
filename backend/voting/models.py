from django.db import models
from django.contrib.auth import get_user_model
from trips.models import Trip
from travel_destinations.models import Destination

User = get_user_model()


class Vote(models.Model):
    """
    One vote per user per trip. A user votes FOR a destination.

    Design decisions:
    - unique_together on (trip, user) — each user gets exactly ONE vote per
      trip. They can CHANGE it (PUT) but not add more. This is the "pick your
      favourite" model, not multi-vote.
    - ForeignKey to Destination (not CharField) so we can aggregate vote
      counts with a simple .values('destination').annotate(count=Count('id'))
      query — no string parsing needed.
    - We intentionally do NOT auto-select a destination when any threshold
      is reached. The group always makes the final decision via the owner.
    """

    trip        = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='votes')
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='votes')
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='votes')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('trip', 'user')   # One vote per user per trip
        verbose_name = 'Vote'
        verbose_name_plural = 'Votes'

    def __str__(self):
        return f"{self.user.username} → {self.destination.name} ({self.trip.name})"
