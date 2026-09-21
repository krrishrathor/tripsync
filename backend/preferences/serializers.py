from rest_framework import serializers
from .models import Preference
from users.serializers import UserSerializer

class PreferenceSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Preference
        fields = (
            'id', 'user', 'trip', 'min_budget', 'max_budget',
            'interests', 'food_preferences', 'accommodation_type',
            'travel_style', 'activity_intensity', 'updated_at'
        )
        read_only_fields = ('id', 'user', 'trip', 'updated_at')
