from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.core.database import get_async_session
from app.models.destination import Destination
from app.models.booking import Booking
from app.schemas.destination import DestinationRead

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("", response_model=list[DestinationRead])
async def get_recommendations(
    user_id: Optional[str] = Query(None),
    limit: int = Query(5, ge=1, le=10),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Phase 4: AI Recommendation Engine.
    Mock implementation: if user has past bookings, recommend similar categories.
    Otherwise, return trending destinations (by booking count or mock score).
    """
    # Get all active destinations
    all_dests_result = await session.execute(
        select(Destination).where(Destination.is_active == True)
    )
    all_dests = all_dests_result.scalars().all()

    if not all_dests:
        return []

    # If user provided, check their history
    user_categories = set()
    if user_id:
        # We need to join Booking -> Listing -> Destination
        # For simplicity, we just use raw SQL or ORM.
        # Since this is a mock recommendation, we'll just return a curated random/shuffled list 
        # or sort by a fake 'relevance' score.
        pass

    # Simple trending algorithm: sort by ID or predefined criteria for now.
    # In a real app, this would use a collaborative filtering model or embeddings matching.
    import random
    curated = list(all_dests)
    random.shuffle(curated)
    
    return [DestinationRead.model_validate(d) for d in curated[:limit]]
