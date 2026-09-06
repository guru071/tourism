from typing import List, Optional
from pydantic import BaseModel


class Activity(BaseModel):
    time_of_day: str  # morning | afternoon | evening
    title: str
    description: str
    location: Optional[str] = None
    duration_hours: float
    estimated_cost_usd: float
    category: str  # dining | sightseeing | adventure | cultural | leisure


class DayPlan(BaseModel):
    day: int
    theme: str
    activities: List[Activity]
    total_estimated_cost_usd: float
    tips: Optional[str] = None


class ItineraryGenerateRequest(BaseModel):
    destination_id: str
    duration_days: int = 3
    travel_style: str = "Cultural"  # Relaxed | Adventure | Cultural | Luxury
    budget_level: str = "Mid-range"  # Budget | Mid-range | Luxury
    notes: Optional[str] = None


class ItineraryRead(BaseModel):
    id: str
    destination_id: str
    duration_days: int
    travel_style: str
    budget_level: str
    title: str
    summary: Optional[str] = None
    day_plans: List[DayPlan]
    total_estimated_cost_usd: float
    destination_name: Optional[str] = None

    model_config = {"from_attributes": True}
