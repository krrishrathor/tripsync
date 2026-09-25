from rest_framework import serializers
from .models import Vote
from travel_destinations.serializers import DestinationSerializer
from users.serializers import UserSerializer


class VoteSerializer(serializers.ModelSerializer):
    """Used for casting / changing a vote (input)."""
    class Meta:
        model  = Vote
        fields = ['id', 'destination', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class VoteSummarySerializer(serializers.Serializer):
    """
    Aggregated vote summary returned by the GET /votes/ endpoint.
    Built manually because it's a query aggregate, not a single model instance.
    """
    destination     = DestinationSerializer()
    vote_count      = serializers.IntegerField()
    vote_pct        = serializers.FloatField()
    voters          = serializers.ListField(child=serializers.DictField())
    current_user_voted = serializers.BooleanField()


class MyVoteSerializer(serializers.Serializer):
    """The currently authenticated user's vote for this trip (or null)."""
    destination_id   = serializers.IntegerField(allow_null=True)
    destination_name = serializers.CharField(allow_null=True)
