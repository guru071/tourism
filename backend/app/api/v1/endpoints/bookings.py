import uuid
from decimal import Decimal
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_async_session
from app.core.security import get_current_user
from app.models.user import User
from app.models.booking import Booking
from app.models.listing import Listing

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post("", status_code=201)
async def create_booking(
    payload: dict,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    listing_result = await session.execute(select(Listing).where(Listing.id == payload["listing_id"]))
    listing = listing_result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if not listing.availability:
        raise HTTPException(status_code=400, detail="Listing is not available")

    try:
        start = date.fromisoformat(payload["check_in_date"])
        end = date.fromisoformat(payload["check_out_date"])
    except (KeyError, ValueError):
        raise HTTPException(status_code=422, detail="Invalid date format. Use YYYY-MM-DD")

    if start >= end:
        raise HTTPException(status_code=422, detail="check_out_date must be after check_in_date")

    guests = int(payload.get("num_guests", 1))
    nights = (end - start).days
    total = float(listing.base_price) * guests * max(nights, 1)

    booking = Booking(
        user_id=current_user.id,
        listing_id=listing.id,
        booking_reference=f"TOS-{str(uuid.uuid4())[:8].upper()}",
        status="pending",
        start_date=start,
        end_date=end,
        guests_count=guests,
        total_price=Decimal(str(total)),
        currency=listing.currency,
        special_requests=payload.get("special_requests"),
    )
    session.add(booking)
    await session.commit()
    await session.refresh(booking)
    return {
        "id": str(booking.id),
        "booking_reference": booking.booking_reference,
        "status": booking.status,
        "listing_title": listing.title,
        "start_date": str(booking.start_date),
        "end_date": str(booking.end_date),
        "guests_count": booking.guests_count,
        "total_price": float(booking.total_price),
        "currency": booking.currency,
    }


@router.get("/my")
async def my_bookings(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(Booking, Listing)
        .join(Listing, Booking.listing_id == Listing.id)
        .where(Booking.user_id == current_user.id)
        .order_by(Booking.created_at.desc())
        .limit(limit).offset(offset)
    )
    results = (await session.execute(stmt)).all()
    return [
        {
            "id": str(b.id),
            "booking_reference": b.booking_reference,
            "listing_title": l.title,
            "status": b.status,
            "start_date": str(b.start_date),
            "end_date": str(b.end_date),
            "guests_count": b.guests_count,
            "total_price": float(b.total_price),
            "currency": b.currency,
        }
        for b, l in results
    ]


@router.get("")
async def list_bookings(
    operator_id: str = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("partner", "admin"):
        raise HTTPException(status_code=403, detail="Access denied")

    stmt = select(Booking, Listing).join(Listing, Booking.listing_id == Listing.id)
    
    if operator_id:
        stmt = stmt.where(Listing.operator_id == operator_id)

    stmt = stmt.order_by(Booking.created_at.desc()).limit(limit).offset(offset)
    results = (await session.execute(stmt)).all()
    
    return [
        {
            "id": str(b.id),
            "booking_reference": b.booking_reference,
            "listing_id": str(l.id),
            "listing_title": l.title,
            "status": b.status,
            "start_date": str(b.start_date),
            "end_date": str(b.end_date),
            "guests_count": b.guests_count,
            "total_price": float(b.total_price),
            "currency": b.currency,
        }
        for b, l in results
    ]


@router.get("/{booking_id}")
async def get_booking(
    booking_id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if str(booking.user_id) != str(current_user.id) and current_user.role not in ("partner", "admin"):
        raise HTTPException(status_code=403, detail="Access denied")
    return {
        "id": str(booking.id),
        "booking_reference": booking.booking_reference,
        "listing_id": str(booking.listing_id),
        "status": booking.status,
        "start_date": str(booking.start_date),
        "end_date": str(booking.end_date),
        "guests_count": booking.guests_count,
        "total_price": float(booking.total_price),
        "currency": booking.currency,
        "special_requests": booking.special_requests,
    }


@router.patch("/{booking_id}/status")
async def update_booking_status(
    booking_id: str,
    payload: dict,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("partner", "admin"):
        raise HTTPException(status_code=403, detail="Only partners or admins can update booking status")

    result = await session.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    new_status = payload.get("status")
    valid_statuses = ("pending", "confirmed", "cancelled", "completed")
    if new_status not in valid_statuses:
        raise HTTPException(status_code=422, detail=f"Status must be one of: {', '.join(valid_statuses)}")

    booking.status = new_status
    await session.commit()
    return {"id": str(booking.id), "status": booking.status, "message": "Status updated"}
