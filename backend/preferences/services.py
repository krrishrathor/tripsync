from collections import Counter
import statistics
from .models import Preference
from trips.models import TripMember

class PreferenceAggregationService:
    @staticmethod
    def aggregate_trip_preferences(trip_id):
        preferences = list(Preference.objects.filter(trip_id=trip_id))
        total_members = TripMember.objects.filter(trip_id=trip_id).count()
        submitted_count = len(preferences)
        
        if submitted_count == 0:
            return {
                "status": "no_data",
                "submitted_count": 0,
                "total_members": total_members
            }
            
        budgets = [float(p.max_budget) for p in preferences if p.max_budget > 0]
        
        # Aggregate arrays
        all_interests = []
        all_food = []
        all_accommodation = []
        travel_styles = []
        
        for p in preferences:
            if isinstance(p.interests, list): all_interests.extend(p.interests)
            if isinstance(p.food_preferences, list): all_food.extend(p.food_preferences)
            if isinstance(p.accommodation_type, list): all_accommodation.extend(p.accommodation_type)
            if p.travel_style: travel_styles.append(p.travel_style)
            
        # Common elements (appearing more than once or most common)
        interest_counts = Counter(all_interests)
        common_interests = [item for item, count in interest_counts.items() if count >= max(1, submitted_count // 2)]
        
        food_counts = Counter(all_food)
        common_food = list(food_counts.keys()) # We want to know all dietary restrictions
        
        accommodation_counts = Counter(all_accommodation)
        preferred_accommodation = [item for item, count in accommodation_counts.items() if count == max(accommodation_counts.values())] if accommodation_counts else []
        
        style_counts = Counter(travel_styles)
        
        # Conflict Detection
        conflicts = []
        # Budget conflict: Check if variance in max_budget is too high
        if budgets and len(budgets) > 1:
            budget_diff = max(budgets) - min(budgets)
            if budget_diff > statistics.median(budgets) * 0.5: # 50% variance
                conflicts.append(f"Significant budget gap (Min: {min(budgets)}, Max: {max(budgets)})")
                
        # Travel style conflict
        if len(style_counts) > 1:
            styles_str = ", ".join([f"{k} ({v})" for k,v in style_counts.items()])
            conflicts.append(f"Mixed travel styles: {styles_str}")

        return {
            "status": "success",
            "submitted_count": submitted_count,
            "total_members": total_members,
            "budget": {
                "average_max": round(statistics.mean(budgets), 2) if budgets else 0,
                "median_max": round(statistics.median(budgets), 2) if budgets else 0,
                "min_acceptable": round(min(budgets), 2) if budgets else 0,
                "all_budgets": budgets
            },
            "interests": {
                "common": common_interests,
                "counts": dict(interest_counts)
            },
            "food_requirements": common_food,
            "preferred_accommodation": preferred_accommodation,
            "conflicts": conflicts
        }
