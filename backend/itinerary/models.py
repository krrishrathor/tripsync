from django.db import models
from trips.models import Trip

class Itinerary(models.Model):
    trip = models.OneToOneField(Trip, on_delete=models.CASCADE, related_name='itinerary')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Itinerary for {self.trip.name}"


class DailyPlan(models.Model):
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name='days')
    day_number = models.PositiveIntegerField()
    date = models.DateField(null=True, blank=True)
    theme = models.CharField(max_length=255, blank=True, help_text="e.g., 'Historical Exploration'")
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['day_number']
        unique_together = ('itinerary', 'day_number')

    def __str__(self):
        return f"Day {self.day_number} - {self.itinerary.trip.name}"


class Activity(models.Model):
    TIME_CHOICES = [
        ('Morning', 'Morning'),
        ('Afternoon', 'Afternoon'),
        ('Evening', 'Evening'),
        ('Night', 'Night'),
    ]

    daily_plan = models.ForeignKey(DailyPlan, on_delete=models.CASCADE, related_name='activities')
    time_of_day = models.CharField(max_length=20, choices=TIME_CHOICES)
    order = models.PositiveIntegerField(default=0, help_text="Order within the time of day")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    location = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['time_of_day', 'order']

    def __str__(self):
        return f"{self.time_of_day}: {self.title}"
