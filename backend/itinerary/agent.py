import os
import json
from typing import TypedDict, List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END

class AgentState(TypedDict):
    trip_id: str
    context: Dict[str, Any]
    draft_itinerary: Optional[List[Dict[str, Any]]]
    feedback: Optional[str]
    iterations: int
    is_valid: bool

# Determine which model to use. If no API key is provided, we'll use a mocked LLM fallback in the node.
# But for the portfolio, we configure the real one.
def get_llm():
    if not os.getenv("OPENAI_API_KEY"):
        return None
    return ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

def generate_draft(state: AgentState):
    """Generates the initial or refined itinerary draft."""
    llm = get_llm()
    context = state["context"]
    feedback = state.get("feedback")
    
    # If no LLM configured, use a deterministic fallback for demo purposes
    if not llm:
        return _mock_generate(state)
        
    days = context.get('duration_days', 3)
    dest_name = context.get('destination_name', 'Unknown')
    budget = context.get('budget_max', 5000)
    
    prompt = f"""
    You are an expert travel agent generating a JSON itinerary.
    Create a {days}-day itinerary for {dest_name}.
    Daily budget should roughly align with ₹{budget}.
    Group Interests: {', '.join(context.get('interests', []))}
    Activity Intensity: {context.get('intensity', 'moderate')}

    Output strictly in this JSON format (no markdown tags, just the JSON array):
    [
      {{
        "day_number": 1,
        "theme": "Arrival & City Center",
        "notes": "Easy walking today.",
        "activities": [
          {{"time_of_day": "Morning", "title": "Check-in", "description": "Arrive at hotel", "estimated_cost": 0, "location": "City Center"}},
          {{"time_of_day": "Afternoon", "title": "Lunch", "description": "Local food", "estimated_cost": 500, "location": "Downtown"}}
        ]
      }}
    ]
    """
    
    if feedback:
        prompt += f"\n\nPrevious draft was rejected with this feedback: {feedback}. Please fix the issues."
        
    messages = [
        SystemMessage(content="You return ONLY raw valid JSON arrays representing the itinerary."),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    content = response.content.strip()
    if content.startswith("```json"):
        content = content[7:-3]
    elif content.startswith("```"):
        content = content[3:-3]
        
    try:
        draft = json.loads(content)
        return {"draft_itinerary": draft, "iterations": state.get("iterations", 0) + 1}
    except Exception as e:
        return {"feedback": f"JSON parse error: {str(e)}", "iterations": state.get("iterations", 0) + 1}

def review_draft(state: AgentState):
    """Validates the draft against hard constraints."""
    draft = state.get("draft_itinerary")
    context = state.get("context", {})
    
    if not draft:
        return {"is_valid": False, "feedback": "Draft is empty."}
        
    expected_days = context.get('duration_days', 3)
    if len(draft) != expected_days:
        return {"is_valid": False, "feedback": f"Generated {len(draft)} days, but expected {expected_days} days."}
        
    for day in draft:
        if 'activities' not in day or not day['activities']:
            return {"is_valid": False, "feedback": f"Day {day.get('day_number')} has no activities."}
            
    # If we made it here, it passed constraints
    return {"is_valid": True, "feedback": None}

def should_continue(state: AgentState):
    """Router to determine next node."""
    if state.get("is_valid"):
        return END
    if state.get("iterations", 0) >= 3:
        # Max retries reached, we just accept what we have or error out
        return END
    return "generate_draft"

def _mock_generate(state: AgentState):
    """Mock fallback if OPENAI_API_KEY is missing, to keep the app working for the user."""
    context = state["context"]
    days = context.get('duration_days', 3)
    dest = context.get('destination_name', 'Destination')
    
    draft = []
    for d in range(1, days + 1):
        draft.append({
            "day_number": d,
            "theme": f"Exploring {dest} - Day {d}",
            "notes": "Auto-generated mock day due to missing OPENAI_API_KEY.",
            "activities": [
                {"time_of_day": "Morning", "title": "Breakfast & Walk", "description": "Local cafe", "estimated_cost": 300, "location": "Downtown"},
                {"time_of_day": "Afternoon", "title": "Sightseeing", "description": "Main attractions", "estimated_cost": 800, "location": "City Center"},
                {"time_of_day": "Evening", "title": "Dinner", "description": "Nice restaurant", "estimated_cost": 1200, "location": "Nearby"}
            ]
        })
    return {"draft_itinerary": draft, "iterations": state.get("iterations", 0) + 1}

# Define the graph
workflow = StateGraph(AgentState)
workflow.add_node("generate_draft", generate_draft)
workflow.add_node("review_draft", review_draft)

workflow.set_entry_point("generate_draft")
workflow.add_edge("generate_draft", "review_draft")
workflow.add_conditional_edges("review_draft", should_continue)

itinerary_agent = workflow.compile()
