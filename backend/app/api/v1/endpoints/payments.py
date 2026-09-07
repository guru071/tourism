from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.core.database import get_async_session
from app.core.security import get_current_user
from app.models.user import User
from app.models.booking import Booking

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("/create-checkout-session")
async def create_checkout_session(
    payload: dict,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """
    Phase 5: Create a Stripe Checkout session for a booking.
    """
    booking_id = payload.get("booking_id")
    if not booking_id:
        raise HTTPException(status_code=422, detail="booking_id required")

    result = await session.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    
    if not booking or str(booking.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Booking not found")
        
    if booking.payment_status == "paid":
        raise HTTPException(status_code=400, detail="Booking is already paid")

    # Mock Stripe session creation
    # In production: stripe.checkout.Session.create(...)
    mock_session_url = f"https://checkout.stripe.com/pay/cs_test_{booking_id[:8]}"
    mock_session_id = f"cs_test_{booking_id[:8]}"

    return {
        "checkout_url": mock_session_url,
        "session_id": mock_session_id
    }

@router.post("/webhook")
async def stripe_webhook(request: Request, session: AsyncSession = Depends(get_async_session)):
    """
    Handle Stripe webhook events (e.g. checkout.session.completed).
    """
    payload = await request.body()
    # In production: verify signature with stripe.Webhook.construct_event(...)
    
    import json
    try:
        event = json.loads(payload)
        
        if event.get("type") == "checkout.session.completed":
            session_data = event.get("data", {}).get("object", {})
            # Mock extracting booking_id from metadata
            # booking_id = session_data.get("metadata", {}).get("booking_id")
            
            # Here we would update booking payment_status to 'paid'
            pass
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    return {"status": "success"}
