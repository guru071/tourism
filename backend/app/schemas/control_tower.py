from typing import List, Optional
from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_users: int
    total_bookings: int
    total_revenue: float
    active_destinations: int
    top_destinations: List[dict]
    booking_status_breakdown: dict


class DestinationAnalytics(BaseModel):
    destination_id: str
    destination_name: str
    visitor_count: int
    revenue: float
    avg_rating: Optional[float]
    booking_trend: List[dict]  # [{week, count}]


class CongestionAlert(BaseModel):
    destination_id: str
    destination_name: str
    bookings_last_7_days: int
    congestion_level: str  # low | medium | high | critical
    threshold: int


class RevenueByMonth(BaseModel):
    month: str
    revenue: float
    booking_count: int
