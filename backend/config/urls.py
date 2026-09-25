"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include
from travel_destinations.urls import trip_urlpatterns as dest_trip_urlpatterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('api/trips/', include('trips.urls')),
    path('api/trips/<uuid:trip_id>/preferences/', include('trip_preferences.urls')),
    path('api/trips/<uuid:trip_id>/', include(dest_trip_urlpatterns)),
    path('api/destinations/', include('travel_destinations.urls')),
]
