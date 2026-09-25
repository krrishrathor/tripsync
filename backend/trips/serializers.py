from rest_framework import serializers
from .models import Trip, TripMember
from users.serializers import UserSerializer

class TripMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = TripMember
        fields = ('id', 'user', 'role', 'joined_at')
        read_only_fields = ('id', 'user', 'role', 'joined_at')

class TripSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    members_count = serializers.SerializerMethodField()
    selected_destination_name = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = (
            'id', 'name', 'description', 'start_date', 'end_date', 
            'total_budget', 'currency', 'status', 'owner', 'invite_code',
            'selected_destination', 'selected_destination_name',
            'created_at', 'updated_at', 'members_count'
        )
        read_only_fields = (
            'id', 'status', 'owner', 'invite_code',
            'selected_destination', 'selected_destination_name',
            'created_at', 'updated_at'
        )

    def get_members_count(self, obj):
        return obj.members.count()

    def get_selected_destination_name(self, obj):
        if obj.selected_destination:
            return obj.selected_destination.name
        return None

class TripDetailSerializer(TripSerializer):
    members = TripMemberSerializer(many=True, read_only=True)

    class Meta(TripSerializer.Meta):
        fields = TripSerializer.Meta.fields + ('members',)
