from django.urls import path
from .views import (
    TripListCreateView, 
    TripDetailView, 
    JoinTripView, 
    GenerateInviteCodeView
)

urlpatterns = [
    path('', TripListCreateView.as_view(), name='trip-list-create'),
    path('<uuid:pk>/', TripDetailView.as_view(), name='trip-detail'),
    path('<uuid:pk>/invite/', GenerateInviteCodeView.as_view(), name='trip-invite'),
    path('join/<str:invite_code>/', JoinTripView.as_view(), name='trip-join'),
]
