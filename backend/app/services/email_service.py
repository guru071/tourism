import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

async def send_booking_confirmation(email: str, booking_ref: str, listing_title: str):
    """
    Phase 5: Send booking confirmation email.
    Mock implementation: In production, integrate with SendGrid or Resend.
    """
    logger.info(f"📧 Sending booking confirmation to {email} for booking {booking_ref} ({listing_title})")
    
    # Example production implementation:
    # if settings.SENDGRID_API_KEY:
    #     message = Mail(
    #         from_email='noreply@tourism.ai',
    #         to_emails=email,
    #         subject='Your Booking Confirmation',
    #         html_content=f'<strong>Booking {booking_ref} confirmed!</strong>'
    #     )
    #     sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    #     response = sg.send(message)

    return True

async def send_review_request(email: str, booking_ref: str, listing_title: str):
    """
    Phase 5: Send review request email after trip completion.
    """
    logger.info(f"📧 Sending review request to {email} for trip {booking_ref} ({listing_title})")
    return True
