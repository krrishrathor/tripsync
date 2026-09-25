from django.db import transaction
from django.utils import timezone
from trips.models import Trip
from trip_preferences.models import MemberPreference
from travel_destinations.models import Destination
from .models import Itinerary, DailyPlan, Activity
from .agent import itinerary_agent

def generate_itinerary_for_trip(trip: Trip):
    """
    Gathers context from the trip, invokes the LangGraph agent,
    and persists the resulting itinerary to the database.
    """
    if trip.status != 'DESTINATION_SELECTED':
        raise ValueError("Cannot generate itinerary unless destination is selected.")
        
    if not trip.selected_destination:
        raise ValueError("Trip has no selected destination.")
        
    # Gather Context
    destination = trip.selected_destination
    
    # Calculate duration
    duration = 3 # default
    if trip.start_date and trip.end_date:
        delta = trip.end_date - trip.start_date
        duration = max(1, delta.days + 1)
        
    # Aggregate preferences (simply taking top interests and average budget)
    prefs = MemberPreference.objects.filter(trip=trip)
    interests = set()
    total_budget = 0
    valid_budgets = 0
    intensity = 'moderate'
    
    for p in prefs:
        if p.interests:
            interests.update(p.interests)
        if p.max_budget:
            total_budget += float(p.max_budget)
            valid_budgets += 1
            
    avg_budget = (total_budget / valid_budgets) if valid_budgets > 0 else 5000
    
    context = {
        'destination_name': destination.name,
        'duration_days': duration,
        'budget_max': avg_budget,
        'interests': list(interests)[:10],
        'intensity': intensity,
    }
    
    # Run Agent
    final_state = itinerary_agent.invoke({
        "trip_id": str(trip.id),
        "context": context,
        "draft_itinerary": None,
        "feedback": None,
        "iterations": 0,
        "is_valid": False
    })
    
    draft = final_state.get('draft_itinerary')
    if not draft:
        raise Exception("Agent failed to generate an itinerary.")
        
    # Persist to Database
    with transaction.atomic():
        # Clear existing itinerary if any
        Itinerary.objects.filter(trip=trip).delete()
        
        itinerary = Itinerary.objects.create(trip=trip)
        
        for day_data in draft:
            day_num = day_data.get('day_number', 1)
            
            # Calculate date for this day
            day_date = None
            if trip.start_date:
                day_date = trip.start_date + timezone.timedelta(days=day_num - 1)
                
            daily_plan = DailyPlan.objects.create(
                itinerary=itinerary,
                day_number=day_num,
                date=day_date,
                theme=day_data.get('theme', '')[:255],
                notes=day_data.get('notes', '')
            )
            
            for idx, act_data in enumerate(day_data.get('activities', [])):
                Activity.objects.create(
                    daily_plan=daily_plan,
                    time_of_day=act_data.get('time_of_day', 'Morning'),
                    order=idx,
                    title=act_data.get('title', '')[:255],
                    description=act_data.get('description', ''),
                    estimated_cost=act_data.get('estimated_cost', 0.0),
                    location=act_data.get('location', '')[:255]
                )
                
        # Update trip status
        trip.status = 'ITINERARY_GENERATED'
        trip.save(update_fields=['status', 'updated_at'])
        
    return itinerary
