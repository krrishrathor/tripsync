import uuid
import secrets
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Trip(models.Model):
    STATUS_CHOICES = [
        ('PLANNING', 'Planning'),
        ('DESTINATION_SELECTED', 'Destination Selected'),
        ('ITINERARY_GENERATED', 'Itinerary Generated'),
        ('COMPLETED', 'Completed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    total_budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='INR')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNING')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_trips')
    invite_code = models.CharField(max_length=10, unique=True, blank=True)
    # Set after the group votes and the owner confirms
    selected_destination = models.ForeignKey(
        'travel_destinations.Destination',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='selected_for_trips',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.invite_code:
            self.invite_code = secrets.token_urlsafe(6)[:8].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class TripMember(models.Model):
    ROLE_CHOICES = [
        ('OWNER', 'Owner'),
        ('MEMBER', 'Member'),
    ]

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trip_memberships')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='MEMBER')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('trip', 'user') # Prevent duplicate memberships

    def __str__(self):
        return f"{self.user.username} - {self.trip.name} ({self.role})"
