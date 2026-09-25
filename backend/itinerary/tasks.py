from celery import shared_task
from django.shortcuts import get_object_or_404
from trips.models import Trip
from .services import generate_itinerary_for_trip

@shared_task
def generate_itinerary_task(trip_id):
    try:
        trip = Trip.objects.get(pk=trip_id)
        # Assuming the status was changed to 'GENERATING_ITINERARY' by the view
        # We call the service, which triggers LangGraph
        generate_itinerary_for_trip(trip)
        return {"status": "success", "trip_id": str(trip_id)}
    except Exception as e:
        # In a real app, we might want to log this or notify the user
        # Let's set trip status back to DESTINATION_SELECTED so they can retry
        trip = Trip.objects.filter(pk=trip_id).first()
        if trip:
            trip.status = 'DESTINATION_SELECTED'
            trip.save(update_fields=['status'])
        return {"status": "error", "message": str(e), "trip_id": str(trip_id)}
