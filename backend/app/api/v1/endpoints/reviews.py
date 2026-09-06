from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.core.database import get_async_session
from app.core.security import get_current_user
from app.models.user import User
from app.models.review import Review
from app.models.listing import Listing

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post("", status_code=201)
async def create_review(
    payload: dict,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    listing_id = payload.get("listing_id")
    rating = int(payload.get("rating", 0))
    if not listing_id:
        raise HTTPException(status_code=422, detail="listing_id is required")
    if not 1 <= rating <= 5:
        raise HTTPException(status_code=422, detail="rating must be between 1 and 5")

    listing_result = await session.execute(select(Listing).where(Listing.id == listing_id))
    listing = listing_result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    review = Review(
        user_id=current_user.id,
        listing_id=listing.id,
        rating=rating,
        comment=payload.get("body") or payload.get("comment"),
    )
    session.add(review)

    # Update listing average rating
    listing.review_count += 1
    listing.rating_average = (
        (float(listing.rating_average) * (listing.review_count - 1) + rating) / listing.review_count
    )

    await session.commit()
    await session.refresh(review)
    return {"id": str(review.id), "rating": review.rating, "message": "Review submitted"}


@router.get("")
async def list_reviews(
    listing_id: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session),
):
    stmt = select(Review)
    if listing_id:
        stmt = stmt.where(Review.listing_id == listing_id)
    stmt = stmt.order_by(Review.created_at.desc()).limit(limit).offset(offset)
    results = (await session.execute(stmt)).scalars().all()
    return [
        {
            "id": str(r.id),
            "user_id": str(r.user_id),
            "listing_id": str(r.listing_id),
            "rating": r.rating,
            "comment": r.comment,
        }
        for r in results
    ]
