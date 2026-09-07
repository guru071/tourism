from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_async_session
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.auth import UserRead

router = APIRouter(prefix="/users", tags=["Admin: Users"])

async def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

@router.get("", response_model=List[UserRead])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(require_admin),
):
    stmt = select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)
    users = (await session.execute(stmt)).scalars().all()
    return [UserRead.model_validate(u) for u in users]

@router.patch("/{user_id}/role")
async def update_user_role(
    user_id: str,
    payload: dict,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(require_admin),
):
    new_role = payload.get("role")
    if new_role not in ("tourist", "partner", "admin"):
        raise HTTPException(status_code=400, detail="Invalid role")

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = new_role
    await session.commit()
    return {"status": "success", "user_id": str(user.id), "new_role": user.role}

@router.patch("/{user_id}/status")
async def toggle_user_status(
    user_id: str,
    payload: dict,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(require_admin),
):
    is_active = payload.get("is_active")
    if is_active is None:
        raise HTTPException(status_code=400, detail="is_active field required")

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = bool(is_active)
    await session.commit()
    return {"status": "success", "user_id": str(user.id), "is_active": user.is_active}
