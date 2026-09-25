from rest_framework import serializers
from .models import Destination


class DestinationSerializer(serializers.ModelSerializer):
    estimated_daily_cost_avg = serializers.IntegerField(read_only=True)

    class Meta:
        model = Destination
        fields = [
            'id', 'name', 'country', 'region', 'description',
            'estimated_daily_cost_min', 'estimated_daily_cost_max', 'estimated_daily_cost_avg',
            'tags', 'popular_activities',
            'best_for_intensity', 'travel_difficulty',
            'recommended_seasons', 'typical_duration_days_min', 'typical_duration_days_max',
            'approximate_travel_hours_from_metro',
            'reachable_by', 'accommodation_available',
            'latitude', 'longitude', 'image_url',
        ]


class ScoredDestinationSerializer(serializers.Serializer):
    """
    Serializes a DestinationScore dataclass alongside the full destination object.
    We build this manually (no ModelSerializer) because DestinationScore is a
    dataclass, not a Django model.
    """
    destination = DestinationSerializer()
    overall     = serializers.IntegerField()
    budget      = serializers.DictField()
    interest    = serializers.DictField()
    duration    = serializers.DictField()
    activity    = serializers.DictField()
    transport   = serializers.DictField()
    accommodation = serializers.DictField()
    conflicts   = serializers.ListField(child=serializers.CharField())
    highlights  = serializers.ListField(child=serializers.CharField())
