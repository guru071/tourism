from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.core.database import get_async_session
from app.models.itinerary import Itinerary
from app.models.destination import Destination
from app.schemas.itinerary import ItineraryGenerateRequest, ItineraryRead
from app.services.gemini_generator import generate_itinerary_gemini

router = APIRouter(prefix="/itineraries", tags=["Itineraries"])


@router.post("/generate", response_model=ItineraryRead, status_code=201)
async def generate(
    payload: ItineraryGenerateRequest,
    session: AsyncSession = Depends(get_async_session),
):
    # Validate destination exists
    result = await session.execute(select(Destination).where(Destination.id == payload.destination_id))
    destination = result.scalar_one_or_none()
    if not destination:
        raise HTTPException(status_code=404, detail="Destination not found")

    if payload.duration_days < 1 or payload.duration_days > 30:
        raise HTTPException(status_code=422, detail="duration_days must be between 1 and 30")

    # Call AI Generator (Gemini + fallback)
    data = await generate_itinerary_gemini(
        destination_name=destination.name,
        destination_id=str(destination.id),
        duration_days=payload.duration_days,
        travel_style=payload.travel_style,
        budget_level=payload.budget_level,
    )

    # Persist to database
    itinerary = Itinerary(
        destination_id=destination.id,
        user_id=None,
        title=data["title"],
        summary=data["summary"],
        duration_days=payload.duration_days,
        travel_style=payload.travel_style,
        budget_level=payload.budget_level,
        day_plans=data["day_plans"],
        total_estimated_cost_usd=data["total_estimated_cost_usd"],
        is_ai_generated=True,
    )
    session.add(itinerary)
    await session.commit()
    await session.refresh(itinerary)

    return ItineraryRead(
        id=str(itinerary.id),
        destination_id=str(itinerary.destination_id),
        duration_days=itinerary.duration_days,
        travel_style=itinerary.travel_style,
        budget_level=itinerary.budget_level,
        title=itinerary.title,
        summary=itinerary.summary,
        day_plans=itinerary.day_plans,
        total_estimated_cost_usd=float(itinerary.total_estimated_cost_usd),
        destination_name=destination.name,
    )


@router.get("/{itinerary_id}", response_model=ItineraryRead)
async def get_itinerary(
    itinerary_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(select(Itinerary).where(Itinerary.id == itinerary_id))
    itinerary = result.scalar_one_or_none()
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    dest_result = await session.execute(select(Destination).where(Destination.id == itinerary.destination_id))
    destination = dest_result.scalar_one_or_none()

    return ItineraryRead(
        id=str(itinerary.id),
        destination_id=str(itinerary.destination_id),
        duration_days=itinerary.duration_days,
        travel_style=itinerary.travel_style,
        budget_level=itinerary.budget_level,
        title=itinerary.title,
        summary=itinerary.summary,
        day_plans=itinerary.day_plans,
        total_estimated_cost_usd=float(itinerary.total_estimated_cost_usd),
        destination_name=destination.name if destination else None,
    )


@router.get("", response_model=list)
async def list_itineraries(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session),
):
    stmt = select(Itinerary).order_by(Itinerary.created_at.desc()).limit(limit).offset(offset)
    results = (await session.execute(stmt)).scalars().all()
    return [{"id": str(i.id), "title": i.title, "duration_days": i.duration_days,
             "travel_style": i.travel_style, "budget_level": i.budget_level,
             "destination_id": str(i.destination_id)} for i in results]
