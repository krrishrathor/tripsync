from rest_framework import serializers
from .models import MemberPreference

VALID_INTERESTS = {
    'beaches', 'mountains', 'adventure', 'nightlife', 'food',
    'photography', 'culture', 'history', 'shopping', 'nature',
    'relaxation', 'sports',
}

VALID_DIETS = {'vegetarian', 'vegan', 'non_vegetarian', 'halal'}


class MemberPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemberPreference
        fields = [
            'id', 'trip', 'user',
            'min_budget', 'max_budget',
            'travel_style', 'preferred_transport', 'max_travel_hours',
            'interests',
            'diet_type', 'food_allergies',
            'accommodation_type', 'activity_intensity',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'trip', 'user', 'created_at', 'updated_at']

    def validate_interests(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Interests must be a list.")
        invalid = set(value) - VALID_INTERESTS
        if invalid:
            raise serializers.ValidationError(
                f"Invalid interests: {invalid}. Valid options: {VALID_INTERESTS}"
            )
        return value

    def validate_diet_type(self, value):
        if value not in VALID_DIETS:
            raise serializers.ValidationError(
                f"Invalid diet type '{value}'. Valid options: {VALID_DIETS}"
            )
        return value

    def validate(self, attrs):
        min_b = attrs.get('min_budget')
        max_b = attrs.get('max_budget')
        if min_b and max_b and min_b > max_b:
            raise serializers.ValidationError(
                {"min_budget": "Minimum budget cannot exceed maximum budget."}
            )
        return attrs
