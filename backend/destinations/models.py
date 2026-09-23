from django.db import models


class Destination(models.Model):
    """
    A seeded (pre-populated) travel destination.

    Design notes:
    - All fields that the scoring engine uses are structured columns —
      NOT stored as a free-form JSON blob. This lets us filter/order
      at the database level and write deterministic unit tests.
    - Tags and popular_activities use JSONField (list of strings) because
      they are purely additive and never aggregated arithmetically.
    - Image URLs are plain strings; in production these would point to a
      CDN. For development they reference Unsplash source URLs.
    """

    # ── Identity ─────────────────────────────────────────────────────────────
    name        = models.CharField(max_length=200)
    country     = models.CharField(max_length=100, default='India')
    region      = models.CharField(max_length=100, blank=True,
                                   help_text="State or geographic region, e.g. 'Rajasthan'")
    description = models.TextField(blank=True)
    image_url   = models.URLField(blank=True)

    # ── Cost ─────────────────────────────────────────────────────────────────
    estimated_daily_cost_min = models.PositiveIntegerField(
        help_text="Minimum daily cost per person in INR (budget traveller)")
    estimated_daily_cost_max = models.PositiveIntegerField(
        help_text="Maximum daily cost per person in INR (luxury traveller)")

    # ── Tags & interests ──────────────────────────────────────────────────────
    # Must use the same vocabulary as MemberPreference.interests
    tags = models.JSONField(default=list,
                            help_text="List of interest tags matching preference vocabulary, "
                                      "e.g. ['beaches', 'nightlife', 'food']")
    popular_activities = models.JSONField(default=list,
                                          help_text="Human-readable activity list for display")

    # ── Travel logistics ──────────────────────────────────────────────────────
    class TravelDifficulty(models.TextChoices):
        EASY     = 'easy',     'Easy'
        MODERATE = 'moderate', 'Moderate'
        HARD     = 'hard',     'Hard / Remote'

    travel_difficulty = models.CharField(max_length=20,
                                         choices=TravelDifficulty.choices,
                                         default=TravelDifficulty.EASY)

    # Typical recommended trip length in days
    recommended_duration_min = models.PositiveIntegerField(default=3)
    recommended_duration_max = models.PositiveIntegerField(default=7)

    # Best seasons to visit (list of month names or 'year-round')
    recommended_seasons = models.JSONField(default=list,
                                           help_text="e.g. ['October', 'November', 'December']")

    # ── Activity intensity profile ────────────────────────────────────────────
    # Describes how adventure-heavy the destination is overall
    # Uses the same vocabulary as MemberPreference.activity_intensity
    activity_intensity_profile = models.CharField(
        max_length=20,
        choices=[('relaxed', 'Relaxed'), ('moderate', 'Moderate'), ('adventurous', 'Adventurous')],
        default='moderate')

    # ── Accommodation range ───────────────────────────────────────────────────
    # Lowest tier available at this destination
    accommodation_min = models.CharField(
        max_length=20,
        choices=[('hostel', 'Hostel'), ('budget', 'Budget Hotel'),
                 ('mid_range', 'Mid-Range'), ('luxury', 'Luxury')],
        default='budget')

    # ── Geography ─────────────────────────────────────────────────────────────
    latitude  = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # ── Meta ──────────────────────────────────────────────────────────────────
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['country']),
            models.Index(fields=['travel_difficulty']),
        ]

    def __str__(self):
        return f"{self.name}, {self.country}"
