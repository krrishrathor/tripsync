from django.db import models
from django.contrib.auth import get_user_model
from trips.models import Trip

User = get_user_model()

class Preference(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trip_preferences')
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='preferences')
    
    # Budgets
    min_budget = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    max_budget = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # JSON arrays for flexible multi-select
    interests = models.JSONField(default=list, blank=True) # e.g., ["beaches", "food", "history"]
    food_preferences = models.JSONField(default=list, blank=True) # e.g., ["vegetarian", "halal"]
    accommodation_type = models.JSONField(default=list, blank=True) # e.g., ["hotel", "resort", "hostel"]
    
    # Single choices
    travel_style = models.CharField(max_length=50, blank=True) # e.g., "relaxed", "packed", "moderate"
    activity_intensity = models.CharField(max_length=50, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'trip') # One preference per user per trip

    def __str__(self):
        return f"Preferences: {self.user.username} for {self.trip.name}"
