from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import datetime, timedelta

from app.core.database import get_async_session
from app.core.security import get_current_user
from app.models.user import User
from app.models.booking import Booking
from app.models.destination import Destination
from app.schemas.control_tower import DashboardStats, CongestionAlert, RevenueByMonth

router = APIRouter(prefix="/control-tower", tags=["Control Tower"])


async def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(require_admin),
):
    total_users = (await session.execute(select(func.count(User.id)))).scalar_one()
    total_bookings = (await session.execute(select(func.count(Booking.id)))).scalar_one()
    total_destinations = (await session.execute(select(func.count(Destination.id)).where(Destination.is_active == True))).scalar_one()

    # Booking status breakdown
    status_results = await session.execute(
        select(Booking.status, func.count(Booking.id)).group_by(Booking.status)
    )
    status_breakdown = {row[0]: row[1] for row in status_results}

    # Top 5 destinations by booking count
    top_dest_result = await session.execute(
        select(Destination.id, Destination.name, func.count(Booking.id).label("booking_count"))
        .join(Booking, Booking.destination_id == Destination.id, isouter=True)
        .group_by(Destination.id, Destination.name)
        .order_by(func.count(Booking.id).desc())
        .limit(5)
    )
    top_destinations = [
        {"id": str(row[0]), "name": row[1], "booking_count": row[2]}
        for row in top_dest_result
    ]

    return DashboardStats(
        total_users=total_users,
        total_bookings=total_bookings,
        total_revenue=0.0,
        active_destinations=total_destinations,
        top_destinations=top_destinations,
        booking_status_breakdown=status_breakdown,
    )


@router.get("/congestion", response_model=list)
async def get_congestion(
    threshold: int = Query(10, description="Bookings in 7 days to flag as high congestion"),
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(require_admin),
):
    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    result = await session.execute(
        select(
            Destination.id,
            Destination.name,
            func.count(Booking.id).label("recent_bookings"),
        )
        .join(Booking, Booking.destination_id == Destination.id, isouter=True)
        .where(Booking.created_at >= seven_days_ago)
        .group_by(Destination.id, Destination.name)
        .order_by(func.count(Booking.id).desc())
    )

    alerts = []
    for row in result:
        count = row[2]
        if count >= threshold * 2:
            level = "critical"
        elif count >= threshold:
            level = "high"
        elif count >= threshold // 2:
            level = "medium"
        else:
            level = "low"
        alerts.append(CongestionAlert(
            destination_id=str(row[0]),
            destination_name=row[1],
            bookings_last_7_days=count,
            congestion_level=level,
            threshold=threshold,
        ).model_dump())

    return alerts


@router.get("/revenue", response_model=list)
async def get_revenue_by_month(
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(require_admin),
):
    # Return last 12 months of revenue grouped by month
    twelve_months_ago = datetime.utcnow() - timedelta(days=365)
    result = await session.execute(
        select(
            func.date_trunc("month", Booking.created_at).label("month"),
            func.count(Booking.id).label("booking_count"),
        )
        .where(Booking.created_at >= twelve_months_ago)
        .group_by(func.date_trunc("month", Booking.created_at))
        .order_by(func.date_trunc("month", Booking.created_at))
    )
    return [
        RevenueByMonth(
            month=str(row[0])[:7] if row[0] else "N/A",
            revenue=0.0,
            booking_count=row[1],
        ).model_dump()
        for row in result
    ]
