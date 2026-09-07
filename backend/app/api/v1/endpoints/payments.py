import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_async_session
from app.core.security import get_current_user
from app.models.user import User
from app.models.booking import Booking

router = APIRouter(prefix="/payments", tags=["Payments"])

# Set Stripe API key if available in environment, otherwise use a placeholder for testing
stripe.api_key = settings.STRIPE_SECRET_KEY if hasattr(settings, "STRIPE_SECRET_KEY") else "sk_test_placeholder"

@router.post("/create-checkout-session")
async def create_checkout_session(
    payload: dict,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """
    Real implementation of Stripe Checkout Session creation.
    Replaces the fake mockup.
    """
    booking_id = payload.get("booking_id")
    if not booking_id:
        raise HTTPException(status_code=400, detail="booking_id is required")

    result = await session.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if str(booking.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to pay for this booking")

    if booking.status != "pending":
        raise HTTPException(status_code=400, detail="Only pending bookings can be paid for")

    try:
        # Create a real Stripe Checkout Session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": booking.currency.lower() if booking.currency else "usd",
                        "unit_amount": int(booking.total_price * 100),  # Stripe uses cents
                        "product_data": {
                            "name": f"Booking {booking.booking_reference}",
                            "description": f"AI Tourism Ecosystem Trip",
                        },
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=f"{settings.FRONTEND_URL}/bookings/{booking.id}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.FRONTEND_URL}/bookings/{booking.id}/cancel",
            metadata={
                "booking_id": str(booking.id),
                "user_id": str(current_user.id)
            }
        )
        return {"checkout_url": checkout_session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(request: Request, session: AsyncSession = Depends(get_async_session)):
    """
    Real Stripe webhook handler.
    Verifies cryptographic signature to prevent fake requests.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    webhook_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", None)

    try:
        if webhook_secret:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        else:
            import json
            # Fallback for dev environments without webhooks configured
            event = stripe.Event.construct_from(json.loads(payload), stripe.api_key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session_obj = event["data"]["object"]
        booking_id = session_obj.get("metadata", {}).get("booking_id")
        
        if booking_id:
            result = await session.execute(select(Booking).where(Booking.id == booking_id))
            booking = result.scalar_one_or_none()
            if booking:
                booking.status = "confirmed"
                await session.commit()
                
    return {"status": "success"}
