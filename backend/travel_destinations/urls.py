from django.urls import path
from .views import DestinationListView, TripCompatibleDestinationsView

urlpatterns = [
    path('', DestinationListView.as_view(), name='destination-list'),
]

# Note: TripCompatibleDestinationsView is mounted under trips URLs in config/urls.py
trip_urlpatterns = [
    path('compatible-destinations/', TripCompatibleDestinationsView.as_view(), name='compatible-destinations'),
]
