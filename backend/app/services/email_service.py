import asyncio
import logging
from typing import Optional

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    from_email: Optional[str] = None,
    plain_text_content: Optional[str] = None,
) -> bool:
    """
    Core email dispatch function using the SendGrid Python package and settings.SENDGRID_API_KEY.
    Executes asynchronously via asyncio.to_thread to prevent blocking the event loop.
    """
    api_key = getattr(settings, "SENDGRID_API_KEY", None)
    if not api_key:
        logger.warning(
            "SENDGRID_API_KEY is not configured in application settings. Email dispatch skipped."
        )
        return False

    sender = from_email or getattr(settings, "SENDGRID_FROM_EMAIL", "noreply@tourism.ai")

    message = Mail(
        from_email=sender,
        to_emails=to_email,
        subject=subject,
        html_content=html_content,
        plain_text_content=plain_text_content,
    )

    try:
        sg = SendGridAPIClient(api_key)
        response = await asyncio.to_thread(sg.send, message)
        logger.info(
            f"SendGrid successfully sent email to {to_email} (status: {response.status_code})"
        )
        return response.status_code in (200, 201, 202)
    except Exception as exc:
        logger.error(f"Failed to send email to {to_email} via SendGrid: {exc}")
        raise


async def send_booking_confirmation(email: str, booking_ref: str, listing_title: str) -> bool:
    """
    Send booking confirmation email to the customer using SendGrid.
    """
    subject = f"Booking Confirmation: {listing_title} ({booking_ref})"
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px; background-color: #ffffff;">
        <h2 style="color: #0f172a; margin-top: 0;">Booking Confirmed!</h2>
        <p style="color: #334155; font-size: 15px; line-height: 1.5;">Hello,</p>
        <p style="color: #334155; font-size: 15px; line-height: 1.5;">Thank you for your reservation. Your booking details are confirmed below:</p>
        <div style="background-color: #f8fafc; border-left: 4px solid #0284c7; padding: 14px 18px; margin: 18px 0; border-radius: 4px;">
            <p style="margin: 4px 0; color: #1e293b; font-size: 15px;"><strong>Experience:</strong> {listing_title}</p>
            <p style="margin: 4px 0; color: #1e293b; font-size: 15px;"><strong>Booking Reference:</strong> {booking_ref}</p>
        </div>
        <p style="color: #334155; font-size: 15px; line-height: 1.5;">You can view and manage your reservation anytime in your Aventis dashboard.</p>
        <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #e2e8f0;">
            <p style="color: #64748b; font-size: 13px; margin: 0;">The Aventis AI Tourism Ecosystem Team</p>
        </div>
    </div>
    """
    return await send_email(to_email=email, subject=subject, html_content=html_content)


async def send_review_request(email: str, booking_ref: str, listing_title: str) -> bool:
    """
    Send review request email after trip completion to solicit traveler feedback using SendGrid.
    """
    subject = f"How was your experience with {listing_title}?"
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px; background-color: #ffffff;">
        <h2 style="color: #0f172a; margin-top: 0;">Share Your Feedback</h2>
        <p style="color: #334155; font-size: 15px; line-height: 1.5;">Hello,</p>
        <p style="color: #334155; font-size: 15px; line-height: 1.5;">We hope you had a wonderful journey with <strong>{listing_title}</strong> (Booking Ref: <strong>{booking_ref}</strong>).</p>
        <p style="color: #334155; font-size: 15px; line-height: 1.5;">Please take a moment to leave a review and share your insights with fellow travelers!</p>
        <div style="margin: 24px 0;">
            <a href="https://tourism.ai/reviews/new?booking_ref={booking_ref}" style="background-color: #0284c7; color: #ffffff; padding: 12px 22px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">Leave a Review</a>
        </div>
        <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #e2e8f0;">
            <p style="color: #64748b; font-size: 13px; margin: 0;">The Aventis AI Tourism Ecosystem Team</p>
        </div>
    </div>
    """
    return await send_email(to_email=email, subject=subject, html_content=html_content)
