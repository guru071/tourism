from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional
import re

from app.core.database import get_async_session
from app.models.destination import Destination
from app.schemas.destination import DestinationCreate, DestinationRead, DestinationList

router = APIRouter(prefix="/destinations", tags=["Destinations"])


def _make_slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


@router.get("", response_model=DestinationList)
async def list_destinations(
    q: Optional[str] = Query(None, description="Search query"),
    category: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session),
):
    stmt = select(Destination).where(Destination.is_active == True)

    if q:
        search = f"%{q}%"
        stmt = stmt.where(
            or_(
                Destination.name.ilike(search),
                Destination.country.ilike(search),
                Destination.city.ilike(search),
                Destination.description.ilike(search),
            )
        )
    if category:
        stmt = stmt.where(Destination.category == category)
    if country:
        stmt = stmt.where(Destination.country.ilike(f"%{country}%"))

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await session.execute(count_stmt)).scalar_one()

    stmt = stmt.order_by(Destination.name).limit(limit).offset(offset)
    results = (await session.execute(stmt)).scalars().all()

    items = []
    for d in results:
        item = DestinationRead.model_validate(d)
        items.append(item)

    return DestinationList(items=items, total=total, limit=limit, offset=offset)


@router.get("/{destination_id}", response_model=DestinationRead)
async def get_destination(
    destination_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(select(Destination).where(Destination.id == destination_id))
    destination = result.scalar_one_or_none()
    if not destination:
        raise HTTPException(status_code=404, detail="Destination not found")
    return DestinationRead.model_validate(destination)


@router.post("", response_model=DestinationRead, status_code=201)
async def create_destination(
    payload: DestinationCreate,
    session: AsyncSession = Depends(get_async_session),
):
    slug = payload.slug or _make_slug(payload.name)
    # ensure slug uniqueness
    existing = await session.execute(select(Destination).where(Destination.slug == slug))
    if existing.scalar_one_or_none():
        slug = f"{slug}-{len(slug)}"

    destination = Destination(
        name=payload.name,
        slug=slug,
        country=payload.country,
        city=payload.city,
        region=payload.region,
        category=payload.category,
        description=payload.description,
        latitude=payload.latitude,
        longitude=payload.longitude,
        timezone=payload.timezone,
        image_urls=payload.image_urls,
        tags=payload.tags,
        is_active=payload.is_active,
    )
    session.add(destination)
    await session.commit()
    await session.refresh(destination)
    return DestinationRead.model_validate(destination)
