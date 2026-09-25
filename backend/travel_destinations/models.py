from django.db import models


class Destination(models.Model):
    """
    Structured destination data.

    Design decisions:
    - Tags and popular_activities are stored as JSONField arrays.
      They are the right case for JSON: unbounded sets with no relational
      queries needed beyond containment checks.
    - Every numeric field used in scoring (estimated_daily_cost,
      typical_duration_days, approximate_travel_hours) is a proper
      numeric column — never a string — so arithmetic in the scoring
      engine never requires parsing or type conversion.
    - recommended_seasons is a JSONField list of month numbers (1-12).
      This keeps the schema tight while allowing flexible "best months" sets.
    """

    # ── Identity ──────────────────────────────────────────────────────────────
    name        = models.CharField(max_length=255, db_index=True)
    country     = models.CharField(max_length=100, default='India')
    region      = models.CharField(max_length=100, blank=True,
                                   help_text="State / geographic region")
    description = models.TextField()

    # ── Cost ──────────────────────────────────────────────────────────────────
    estimated_daily_cost_min = models.PositiveIntegerField(
        help_text="Minimum estimated per-person daily cost (INR)")
    estimated_daily_cost_max = models.PositiveIntegerField(
        help_text="Maximum estimated per-person daily cost (INR)")

    # ── Classification ────────────────────────────────────────────────────────
    # tags: list of strings from the same interest vocabulary used in preferences
    # e.g. ["beaches", "food", "nightlife"]
    tags = models.JSONField(default=list,
                            help_text="Interest tags matching preference interests vocabulary")

    popular_activities = models.JSONField(default=list,
                                          help_text="List of activity name strings")

    # best for: relaxed | moderate | adventurous (maps to activity_intensity)
    best_for_intensity = models.CharField(
        max_length=20,
        choices=[('relaxed', 'Relaxed'), ('moderate', 'Moderate'), ('adventurous', 'Adventurous')],
        default='moderate',
    )

    # ── Logistics ─────────────────────────────────────────────────────────────
    travel_difficulty = models.CharField(
        max_length=10,
        choices=[('easy', 'Easy'), ('moderate', 'Moderate'), ('hard', 'Hard')],
        default='easy',
    )
    recommended_seasons = models.JSONField(
        default=list,
        help_text="List of best-visit month numbers (1=Jan … 12=Dec)")
    typical_duration_days_min = models.PositiveIntegerField(default=3)
    typical_duration_days_max = models.PositiveIntegerField(default=7)
    approximate_travel_hours_from_metro = models.FloatField(
        null=True, blank=True,
        help_text="Approximate one-way travel time by common transport from nearest major metro (hours)")

    # ── Primary transport options ─────────────────────────────────────────────
    # e.g. ["flight", "train", "road"]
    reachable_by = models.JSONField(default=list)

    # ── Accommodation availability ─────────────────────────────────────────────
    # e.g. ["hostel", "budget", "mid_range", "luxury"]
    accommodation_available = models.JSONField(default=list)

    # ── Geography ─────────────────────────────────────────────────────────────
    latitude  = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # ── Media ─────────────────────────────────────────────────────────────────
    image_url = models.URLField(blank=True,
                                help_text="Unsplash or CDN URL for destination card image")

    # ── Meta ──────────────────────────────────────────────────────────────────
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Destination'
        verbose_name_plural = 'Destinations'

    def __str__(self):
        return f"{self.name}, {self.region or self.country}"

    @property
    def estimated_daily_cost_avg(self):
        return (self.estimated_daily_cost_min + self.estimated_daily_cost_max) // 2
