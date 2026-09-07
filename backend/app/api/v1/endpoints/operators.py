from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.core.database import get_async_session
from app.core.security import get_current_user
from app.models.user import User
from app.models.operator import Operator
from app.models.listing import Listing

router = APIRouter(prefix="/operators", tags=["Operators"])


@router.get("")
async def list_operators(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session),
):
    stmt = select(Operator).order_by(Operator.business_name).limit(limit).offset(offset)
    results = (await session.execute(stmt)).scalars().all()
    return [
        {
            "id": str(op.id),
            "business_name": op.business_name,
            "business_type": op.business_type,
            "description": op.description,
            "contact_email": op.contact_email,
            "website_url": op.website_url,
            "verified": op.verified,
            "verification_status": op.verification_status,
        }
        for op in results
    ]
@router.get("/my")
async def get_my_operator(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(select(Operator).where(Operator.user_id == current_user.id))
    op = result.scalar_one_or_none()
    if not op:
        raise HTTPException(status_code=404, detail="Operator profile not found")

    listings_result = await session.execute(
        select(Listing).where(Listing.operator_id == op.id, Listing.is_active == True)
    )
    listings = listings_result.scalars().all()

    return {
        "id": str(op.id),
        "business_name": op.business_name,
        "business_type": op.business_type,
        "description": op.description,
        "contact_email": op.contact_email,
        "contact_phone": op.contact_phone,
        "website_url": op.website_url,
        "verified": op.verified,
        "verification_status": op.verification_status,
        "listings": [
            {
                "id": str(l.id),
                "title": l.title,
                "category": l.category,
                "base_price": float(l.base_price),
                "currency": l.currency,
                "availability": l.availability,
                "rating_average": float(l.rating_average),
                "review_count": l.review_count,
            }
            for l in listings
        ],
    }


@router.get("/{operator_id}")
async def get_operator(
    operator_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(select(Operator).where(Operator.id == operator_id))
    op = result.scalar_one_or_none()
    if not op:
        raise HTTPException(status_code=404, detail="Operator not found")

    # Get their listings
    listings_result = await session.execute(
        select(Listing).where(Listing.operator_id == op.id, Listing.is_active == True)
    )
    listings = listings_result.scalars().all()

    return {
        "id": str(op.id),
        "business_name": op.business_name,
        "business_type": op.business_type,
        "description": op.description,
        "contact_email": op.contact_email,
        "contact_phone": op.contact_phone,
        "website_url": op.website_url,
        "verified": op.verified,
        "verification_status": op.verification_status,
        "listings": [
            {
                "id": str(l.id),
                "title": l.title,
                "category": l.category,
                "base_price": float(l.base_price),
                "currency": l.currency,
                "availability": l.availability,
                "rating_average": float(l.rating_average),
                "review_count": l.review_count,
            }
            for l in listings
        ],
    }


@router.post("", status_code=201)
async def create_operator(
    payload: dict,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("partner", "admin"):
        raise HTTPException(status_code=403, detail="Only partners can create operator profiles")

    existing = await session.execute(select(Operator).where(Operator.user_id == current_user.id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Operator profile already exists for this user")

    op = Operator(
        user_id=current_user.id,
        business_name=payload.get("business_name", ""),
        business_type=payload.get("business_type", "agency"),
        description=payload.get("description"),
        contact_email=payload.get("contact_email", current_user.email),
        contact_phone=payload.get("contact_phone"),
        website_url=payload.get("website_url"),
    )
    session.add(op)
    await session.commit()
    await session.refresh(op)
    return {"id": str(op.id), "business_name": op.business_name, "verification_status": op.verification_status}

@router.patch("/{operator_id}/verify")
async def verify_operator(
    operator_id: str,
    payload: dict,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Admin only: Verify or reject an operator profile."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
        
    status = payload.get("status")
    if status not in ("approved", "rejected", "pending"):
        raise HTTPException(status_code=400, detail="Invalid verification status")

    result = await session.execute(select(Operator).where(Operator.id == operator_id))
    op = result.scalar_one_or_none()
    if not op:
        raise HTTPException(status_code=404, detail="Operator not found")

    op.verification_status = status
    op.verified = (status == "approved")
    await session.commit()
    return {"status": "success", "operator_id": str(op.id), "verification_status": op.verification_status, "verified": op.verified}
