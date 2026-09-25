from django.urls import path
from .views import ItineraryView, GenerateItineraryView

urlpatterns = [
    path('', ItineraryView.as_view(), name='trip-itinerary'),
    path('generate/', GenerateItineraryView.as_view(), name='generate-itinerary'),
]
