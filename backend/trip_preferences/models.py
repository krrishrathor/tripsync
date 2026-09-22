from django.db import models
from django.contrib.auth import get_user_model
from trips.models import Trip

User = get_user_model()

# ─────────────────────────────────────────────────────────────────────────────
# Choices – kept as module-level constants so the aggregation service can
# reference them without importing the model (breaks circular imports).
# ─────────────────────────────────────────────────────────────────────────────

class TravelStyle(models.TextChoices):
    BUDGET      = 'budget',      'Budget Backpacker'
    MID_RANGE   = 'mid_range',   'Mid Range'
    LUXURY      = 'luxury',      'Luxury'

class TransportMode(models.TextChoices):
    FLIGHT  = 'flight',  'Flight'
    TRAIN   = 'train',   'Train'
    BUS     = 'bus',     'Bus'
    ROAD    = 'road',    'Road Trip (Car/Bike)'
    ANY     = 'any',     'No Preference'

class ActivityIntensity(models.TextChoices):
    RELAXED     = 'relaxed',     'Relaxed (minimal exertion)'
    MODERATE    = 'moderate',    'Moderate (some walking/activity)'
    ADVENTUROUS = 'adventurous', 'Adventurous (high activity)'

class AccommodationType(models.TextChoices):
    HOSTEL    = 'hostel',    'Hostel'
    BUDGET    = 'budget',    'Budget Hotel'
    MID_RANGE = 'mid_range', 'Mid-Range Hotel'
    LUXURY    = 'luxury',    'Luxury Hotel / Resort'
    APARTMENT = 'apartment', 'Apartment / Airbnb'


class MemberPreference(models.Model):
    """
    Stores one user's preferences for one specific trip.

    Design decision:
    - Structured scalar fields (budget, travel_style, etc.) are stored as
      dedicated DB columns. This lets the aggregation service query/filter
      at the database level rather than pulling every row into Python.
    - Multi-select fields (interests, food restrictions) are stored as
      JSONField arrays. They are still validated by the serializer, but a
      JSONField gives the flexibility to expand the option set without
      adding columns.
    - We avoid a flat JSON blob for everything because that makes queries,
      validation, and aggregation far harder.
    """

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='member_preferences')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trip_preferences')

    # ── Budget ────────────────────────────────────────────────────────────────
    min_budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                     help_text="Minimum acceptable total trip spend (INR or trip currency)")
    max_budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                     help_text="Maximum the user is willing to spend")

    # ── Travel style & logistics ───────────────────────────────────────────────
    travel_style       = models.CharField(max_length=20, choices=TravelStyle.choices,
                                          default=TravelStyle.MID_RANGE)
    preferred_transport = models.CharField(max_length=20, choices=TransportMode.choices,
                                           default=TransportMode.ANY)
    max_travel_hours   = models.PositiveIntegerField(null=True, blank=True,
                                                     help_text="Maximum hours willing to travel (one way)")

    # ── Interests (multi-select stored as JSON array) ─────────────────────────
    # Valid values: beaches, mountains, adventure, nightlife, food, photography,
    #               culture, history, shopping, nature, relaxation, sports
    interests = models.JSONField(default=list, blank=True)

    # ── Food preferences ──────────────────────────────────────────────────────
    # diet_type valid values: vegetarian, vegan, non_vegetarian, halal
    diet_type    = models.CharField(max_length=20, default='non_vegetarian')
    food_allergies = models.JSONField(default=list, blank=True,
                                      help_text="List of allergy strings e.g. ['nuts', 'gluten']")

    # ── Accommodation ─────────────────────────────────────────────────────────
    accommodation_type = models.CharField(max_length=20, choices=AccommodationType.choices,
                                          default=AccommodationType.MID_RANGE)

    # ── Activity intensity ────────────────────────────────────────────────────
    activity_intensity = models.CharField(max_length=20, choices=ActivityIntensity.choices,
                                          default=ActivityIntensity.MODERATE)

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('trip', 'user')   # One preference set per user per trip
        verbose_name = 'Member Preference'
        verbose_name_plural = 'Member Preferences'

    def __str__(self):
        return f"{self.user.username} preferences for {self.trip.name}"
