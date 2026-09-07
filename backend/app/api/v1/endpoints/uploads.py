from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
import uuid
import time
import hmac
import hashlib
from base64 import b64encode

from app.core.security import get_current_user
from app.models.user import User
from app.core.config import settings

router = APIRouter(prefix="/uploads", tags=["Uploads"])

@router.get("/presigned-url")
async def get_presigned_url(
    filename: str,
    content_type: str,
    current_user: User = Depends(get_current_user)
):
    """
    Phase 5: Generates a presigned URL for direct client-to-storage uploads.
    Mock implementation: In production, this would use boto3 with AWS S3 or Cloudflare R2.
    """
    if current_user.role not in ("admin", "partner"):
        raise HTTPException(status_code=403, detail="Not authorized to upload files")

    # Generate a unique object key
    ext = filename.split(".")[-1] if "." in filename else "bin"
    object_key = f"uploads/{current_user.id}/{int(time.time())}_{uuid.uuid4().hex[:8]}.{ext}"

    # Mock presigned URL generation (replace with boto3.client('s3').generate_presigned_url)
    mock_upload_url = f"https://storage.tourism.ai/mock-bucket/{object_key}?signature=mock_sig"
    mock_public_url = f"https://cdn.tourism.ai/{object_key}"

    return {
        "upload_url": mock_upload_url,
        "public_url": mock_public_url,
        "object_key": object_key,
        "expires_in": 3600
    }
