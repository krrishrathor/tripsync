from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Trip, TripMember
from .serializers import TripSerializer, TripDetailSerializer
from .permissions import IsTripMemberOrOwner, IsTripOwner

class TripListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        return TripSerializer

    def get_queryset(self):
        # Return trips where the user is a member
        return Trip.objects.filter(members__user=self.request.user).distinct()

    def perform_create(self, serializer):
        # Create the trip and automatically add the creator as the OWNER
        trip = serializer.save(owner=self.request.user)
        TripMember.objects.create(trip=trip, user=self.request.user, role='OWNER')

class TripDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Trip.objects.all()
    serializer_class = TripDetailSerializer
    
    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            # Only owner can update or delete
            return [permissions.IsAuthenticated(), IsTripOwner()]
        # Any member can view
        return [permissions.IsAuthenticated(), IsTripMemberOrOwner()]

class JoinTripView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, invite_code):
        trip = get_object_or_404(Trip, invite_code=invite_code)
        
        # Check if user is already a member
        if TripMember.objects.filter(trip=trip, user=request.user).exists():
            return Response({"detail": "You are already a member of this trip."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create membership
        TripMember.objects.create(trip=trip, user=request.user, role='MEMBER')
        
        return Response({
            "detail": "Successfully joined the trip.",
            "trip_id": trip.id,
            "trip_name": trip.name
        }, status=status.HTTP_200_OK)

class GenerateInviteCodeView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTripOwner]

    def post(self, request, pk):
        trip = get_object_or_404(Trip, pk=pk)
        
        # Check permission manually because it's not a generic view
        self.check_object_permissions(request, trip)
        
        import secrets
        trip.invite_code = secrets.token_urlsafe(6)[:8].upper()
        trip.save()
        
        return Response({"invite_code": trip.invite_code}, status=status.HTTP_200_OK)
