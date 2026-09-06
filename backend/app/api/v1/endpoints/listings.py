import re
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import Optional

from app.core.database import get_async_session
from app.core.security import get_current_user
from app.models.user import User
from app.models.listing import Listing
from app.models.operator import Operator

router = APIRouter(prefix="/listings", tags=["Listings"])


def _make_slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


@router.get("")
async def list_listings(
    operator_id: Optional[str] = Query(None),
    destination_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session),
):
    stmt = select(Listing).where(Listing.is_active == True)
    if operator_id:
        stmt = stmt.where(Listing.operator_id == operator_id)
    if destination_id:
        stmt = stmt.where(Listing.destination_id == destination_id)
    if category:
        stmt = stmt.where(Listing.category == category)
    if min_price is not None:
        stmt = stmt.where(Listing.base_price >= Decimal(str(min_price)))
    if max_price is not None:
        stmt = stmt.where(Listing.base_price <= Decimal(str(max_price)))

    stmt = stmt.order_by(Listing.title).limit(limit).offset(offset)
    results = (await session.execute(stmt)).scalars().all()
    return [
        {
            "id": str(l.id),
            "operator_id": str(l.operator_id),
            "destination_id": str(l.destination_id),
            "title": l.title,
            "category": l.category,
            "description": l.description,
            "base_price": float(l.base_price),
            "currency": l.currency,
            "availability": l.availability,
            "capacity": l.capacity,
            "duration_hours": float(l.duration_hours) if l.duration_hours else None,
            "images": l.images,
            "amenities": l.amenities,
            "rating_average": float(l.rating_average),
            "review_count": l.review_count,
        }
        for l in results
    ]


@router.get("/{listing_id}")
async def get_listing(
    listing_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(select(Listing).where(Listing.id == listing_id))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return {
        "id": str(listing.id),
        "operator_id": str(listing.operator_id),
        "destination_id": str(listing.destination_id),
        "title": listing.title,
        "slug": listing.slug,
        "category": listing.category,
        "description": listing.description,
        "base_price": float(listing.base_price),
        "currency": listing.currency,
        "availability": listing.availability,
        "capacity": listing.capacity,
        "duration_hours": float(listing.duration_hours) if listing.duration_hours else None,
        "images": listing.images,
        "amenities": listing.amenities,
        "is_active": listing.is_active,
        "rating_average": float(listing.rating_average),
        "review_count": listing.review_count,
    }


@router.post("", status_code=201)
async def create_listing(
    payload: dict,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("partner", "admin"):
        raise HTTPException(status_code=403, detail="Only partners can create listings")

    op_result = await session.execute(select(Operator).where(Operator.user_id == current_user.id))
    operator = op_result.scalar_one_or_none()
    if not operator:
        raise HTTPException(status_code=400, detail="Create an operator profile first")

    slug = _make_slug(payload.get("title", "listing"))
    existing = await session.execute(select(Listing).where(Listing.slug == slug))
    if existing.scalar_one_or_none():
        slug = f"{slug}-{str(operator.id)[:8]}"

    listing = Listing(
        operator_id=operator.id,
        destination_id=payload["destination_id"],
        title=payload["title"],
        slug=slug,
        category=payload.get("category", "tour"),
        description=payload.get("description", ""),
        base_price=Decimal(str(payload.get("base_price", "0"))),
        currency=payload.get("currency", "USD"),
        capacity=payload.get("capacity"),
        duration_hours=Decimal(str(payload["duration_hours"])) if payload.get("duration_hours") else None,
        images=payload.get("images", []),
        amenities=payload.get("amenities", []),
    )
    session.add(listing)
    await session.commit()
    await session.refresh(listing)
    return {"id": str(listing.id), "title": listing.title, "slug": listing.slug}


@router.put("/{listing_id}")
async def update_listing(
    listing_id: str,
    payload: dict,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(select(Listing).where(Listing.id == listing_id))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    # Only owner or admin
    op_result = await session.execute(select(Operator).where(Operator.user_id == current_user.id))
    operator = op_result.scalar_one_or_none()
    if current_user.role != "admin" and (not operator or str(operator.id) != str(listing.operator_id)):
        raise HTTPException(status_code=403, detail="You can only edit your own listings")

    for field in ("title", "description", "category", "availability", "capacity", "images", "amenities"):
        if field in payload:
            setattr(listing, field, payload[field])
    if "base_price" in payload:
        listing.base_price = Decimal(str(payload["base_price"]))

    await session.commit()
    return {"id": str(listing.id), "title": listing.title, "message": "Updated successfully"}
