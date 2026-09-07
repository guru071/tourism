import os
import pytest
from unittest.mock import MagicMock, patch
from starlette.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.services.email_service import (
    send_email,
    send_booking_confirmation,
    send_review_request,
)
from app.api.v1.endpoints.uploads import (
    get_s3_client,
    generate_s3_presigned_url,
)


# ==============================================================================
# S3 / Cloudflare R2 Uploads Verification
# ==============================================================================

def test_s3_presigned_url_generation_configured_via_env(monkeypatch):
    """
    Verifies that real AWS S3 presigned URLs are generated using boto3.client('s3')
    configured via AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, and S3_BUCKET_NAME.
    """
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test-access-key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test-secret-key")
    monkeypatch.setenv("AWS_REGION", "us-west-2")
    monkeypatch.setenv("S3_BUCKET_NAME", "my-production-bucket")
    monkeypatch.delenv("S3_ENDPOINT_URL", raising=False)
    monkeypatch.delenv("AWS_ENDPOINT_URL", raising=False)
    monkeypatch.delenv("R2_ENDPOINT_URL", raising=False)
    monkeypatch.delenv("CDN_DOMAIN", raising=False)

    upload_url, public_url = generate_s3_presigned_url(
        bucket_name="my-production-bucket",
        object_key="uploads/partner-1/photo.jpg",
        content_type="image/jpeg",
        expires_in=3600,
    )

    assert "my-production-bucket.s3.amazonaws.com" in upload_url or "my-production-bucket.s3.us-west-2.amazonaws.com" in upload_url
    assert "uploads/partner-1/photo.jpg" in upload_url
    assert "X-Amz-Signature=" in upload_url
    assert "X-Amz-Credential=" in upload_url
    assert "test-access-key" in upload_url
    assert "us-west-2" in upload_url
    assert public_url == "https://my-production-bucket.s3.us-west-2.amazonaws.com/uploads/partner-1/photo.jpg"


def test_cloudflare_r2_presigned_url_generation(monkeypatch):
    """
    Verifies Cloudflare R2 S3-compatible presigned URL generation with custom endpoint.
    """
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "r2-test-key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "r2-test-secret")
    monkeypatch.setenv("AWS_REGION", "auto")
    monkeypatch.setenv("S3_BUCKET_NAME", "my-r2-bucket")
    monkeypatch.setenv("S3_ENDPOINT_URL", "https://xyz123.r2.cloudflarestorage.com")

    upload_url, public_url = generate_s3_presigned_url(
        bucket_name="my-r2-bucket",
        object_key="uploads/user-99/avatar.png",
        content_type="image/png",
        expires_in=1800,
    )

    assert "https://xyz123.r2.cloudflarestorage.com/my-r2-bucket/uploads/user-99/avatar.png" in upload_url
    assert "X-Amz-Signature=" in upload_url
    assert "r2-test-key" in upload_url
    assert public_url == "https://xyz123.r2.cloudflarestorage.com/my-r2-bucket/uploads/user-99/avatar.png"


def test_uploads_endpoint_with_s3_credentials(monkeypatch):
    """
    Tests POST /api/v1/uploads endpoint when S3 credentials are configured in environment.
    """
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "env-key-123")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "env-secret-456")
    monkeypatch.setenv("AWS_REGION", "eu-central-1")
    monkeypatch.setenv("S3_BUCKET_NAME", "aventis-travel-assets")

    client = TestClient(app)
    response = client.post(
        "/api/v1/uploads",
        json={"filename": "sunset.webp", "content_type": "image/webp"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "upload_url" in data
    assert "public_url" in data
    assert "object_key" in data
    assert "aventis-travel-assets" in data["upload_url"]
    assert "X-Amz-Signature=" in data["upload_url"]
    assert "eu-central-1" in data["upload_url"]
    assert data["public_url"].startswith("https://aventis-travel-assets.s3.eu-central-1.amazonaws.com/")


# ==============================================================================
# SendGrid Email Service Verification
# ==============================================================================

@pytest.mark.asyncio
async def test_email_service_without_api_key(monkeypatch):
    """
    When SENDGRID_API_KEY is not configured, email functions should log warning and return False.
    """
    monkeypatch.setattr(settings, "SENDGRID_API_KEY", "")
    result = await send_booking_confirmation("traveler@example.com", "BK-9999", "Swiss Alps Tour")
    assert result is False

    review_result = await send_review_request("traveler@example.com", "BK-9999", "Swiss Alps Tour")
    assert review_result is False


@pytest.mark.asyncio
async def test_email_service_with_sendgrid_dispatch(monkeypatch):
    """
    When SENDGRID_API_KEY is configured, actual email dispatch is invoked using SendGridAPIClient.
    """
    monkeypatch.setattr(settings, "SENDGRID_API_KEY", "SG.test_mock_api_key_12345")
    monkeypatch.setattr(settings, "SENDGRID_FROM_EMAIL", "bookings@aventis.ai")

    mock_send_response = MagicMock()
    mock_send_response.status_code = 202

    with patch("app.services.email_service.SendGridAPIClient") as mock_sg_cls:
        mock_instance = MagicMock()
        mock_instance.send.return_value = mock_send_response
        mock_sg_cls.return_value = mock_instance

        # Test booking confirmation
        success = await send_booking_confirmation(
            email="explorer@destination.com",
            booking_ref="BK-2026-X8",
            listing_title="Serengeti Safari",
        )
        assert success is True
        mock_sg_cls.assert_called_once_with("SG.test_mock_api_key_12345")
        mock_instance.send.assert_called_once()
        sent_mail = mock_instance.send.call_args[0][0]
        assert sent_mail.from_email.email == "bookings@aventis.ai"
        assert "BK-2026-X8" in sent_mail.subject.get()


@pytest.mark.asyncio
async def test_send_review_request_with_sendgrid_dispatch(monkeypatch):
    """
    Verifies send_review_request constructs valid Mail and invokes SendGrid.
    """
    monkeypatch.setattr(settings, "SENDGRID_API_KEY", "SG.test_mock_api_key_12345")

    mock_send_response = MagicMock()
    mock_send_response.status_code = 200

    with patch("app.services.email_service.SendGridAPIClient") as mock_sg_cls:
        mock_instance = MagicMock()
        mock_instance.send.return_value = mock_send_response
        mock_sg_cls.return_value = mock_instance

        success = await send_review_request(
            email="guest@paradise.org",
            booking_ref="BK-777",
            listing_title="Kyoto Tea Ceremony",
        )
        assert success is True
        mock_sg_cls.assert_called_once_with("SG.test_mock_api_key_12345")
        mock_instance.send.assert_called_once()
        sent_mail = mock_instance.send.call_args[0][0]
        assert "Kyoto Tea Ceremony" in sent_mail.subject.get()
