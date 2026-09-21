from rest_framework import permissions
from .models import TripMember

class IsTripMemberOrOwner(permissions.BasePermission):
    """
    Custom permission to only allow members of a trip to access it.
    """
    def has_object_permission(self, request, view, obj):
        # obj is a Trip instance
        return TripMember.objects.filter(trip=obj, user=request.user).exists()

class IsTripOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of a trip to edit it.
    """
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user
