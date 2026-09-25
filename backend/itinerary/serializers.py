from rest_framework import serializers
from .models import Itinerary, DailyPlan, Activity

class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = ['id', 'time_of_day', 'order', 'title', 'description', 'estimated_cost', 'location']

class DailyPlanSerializer(serializers.ModelSerializer):
    activities = ActivitySerializer(many=True, read_only=True)
    
    class Meta:
        model = DailyPlan
        fields = ['id', 'day_number', 'date', 'theme', 'notes', 'activities']

class ItinerarySerializer(serializers.ModelSerializer):
    days = DailyPlanSerializer(many=True, read_only=True)
    
    class Meta:
        model = Itinerary
        fields = ['id', 'trip_id', 'created_at', 'updated_at', 'days']
