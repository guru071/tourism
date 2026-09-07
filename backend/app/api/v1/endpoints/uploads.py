import os
import uuid
import time
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, BotoCoreError, NoCredentialsError

from app.core.config import settings
from app.core.database import get_async_session
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/uploads", tags=["Uploads"])

UPLOAD_STORAGE_DIR = os.path.join(os.getcwd(), "storage", "uploads")
os.makedirs(UPLOAD_STORAGE_DIR, exist_ok=True)


class UploadPresignRequest(BaseModel):
    filename: str
    content_type: Optional[str] = "image/jpeg"


async def get_optional_user(
    request: Request,
    session: AsyncSession = Depends(get_async_session)
) -> Optional[User]:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id:
            result = await session.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()
    except Exception:
        return None
    return None


def get_s3_client():
    """
    Initializes and returns a boto3 S3 client configured with AWS / Cloudflare R2 credentials.
    Configured via AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, and optional endpoint URL.
    """
    aws_access_key_id = (
        os.getenv("AWS_ACCESS_KEY_ID")
        or os.getenv("R2_ACCESS_KEY_ID")
        or getattr(settings, "AWS_ACCESS_KEY_ID", None)
    )
    aws_secret_access_key = (
        os.getenv("AWS_SECRET_ACCESS_KEY")
        or os.getenv("R2_SECRET_ACCESS_KEY")
        or getattr(settings, "AWS_SECRET_ACCESS_KEY", None)
    )
    aws_region = (
        os.getenv("AWS_REGION")
        or getattr(settings, "AWS_REGION", "us-east-1")
    )
    endpoint_url = (
        os.getenv("S3_ENDPOINT_URL")
        or os.getenv("AWS_ENDPOINT_URL")
        or os.getenv("R2_ENDPOINT_URL")
        or getattr(settings, "S3_ENDPOINT_URL", None)
    )

    client_kwargs = {
        "region_name": aws_region,
        "config": Config(signature_version="s3v4"),
    }
    if aws_access_key_id and aws_secret_access_key:
        client_kwargs["aws_access_key_id"] = aws_access_key_id
        client_kwargs["aws_secret_access_key"] = aws_secret_access_key
    if endpoint_url:
        client_kwargs["endpoint_url"] = endpoint_url

    return boto3.client("s3", **client_kwargs)


def generate_s3_presigned_url(
    bucket_name: str,
    object_key: str,
    content_type: str,
    expires_in: int = 3600,
) -> tuple[str, str]:
    """
    Generates a real AWS S3 or Cloudflare R2 presigned PUT upload URL and its corresponding public URL.
    """
    aws_region = os.getenv("AWS_REGION") or getattr(settings, "AWS_REGION", "us-east-1")
    endpoint_url = (
        os.getenv("S3_ENDPOINT_URL")
        or os.getenv("AWS_ENDPOINT_URL")
        or os.getenv("R2_ENDPOINT_URL")
        or getattr(settings, "S3_ENDPOINT_URL", None)
    )
    cdn_domain = (
        os.getenv("CDN_DOMAIN")
        or os.getenv("S3_PUBLIC_URL_PREFIX")
        or getattr(settings, "S3_PUBLIC_URL_PREFIX", None)
    )

    s3_client = get_s3_client()
    upload_url = s3_client.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": bucket_name,
            "Key": object_key,
            "ContentType": content_type,
        },
        ExpiresIn=expires_in,
    )

    if cdn_domain:
        cdn = cdn_domain.replace("https://", "").replace("http://", "").rstrip("/")
        public_url = f"https://{cdn}/{object_key}"
    elif endpoint_url:
        public_url = f"{endpoint_url.rstrip('/')}/{bucket_name}/{object_key}"
    else:
        public_url = f"https://{bucket_name}.s3.{aws_region}.amazonaws.com/{object_key}"

    return upload_url, public_url


@router.post("")
@router.post("/")
@router.post("/presigned-url")
async def create_presigned_url(
    payload: UploadPresignRequest,
    request: Request,
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Generates a presigned URL for direct client-to-storage uploads.
    Supports real AWS S3 / Cloudflare R2 presigned URLs when configured,
    and falls back to local binary storage in offline / development environments.
    """
    if current_user and current_user.role not in ("admin", "partner", "operator"):
        raise HTTPException(status_code=403, detail="Not authorized to upload files")

    user_id = str(current_user.id) if current_user else "partner-upload"
    filename = payload.filename or "upload.jpg"
    ext = filename.split(".")[-1].lower() if "." in filename else "jpg"

    if ext not in ("jpg", "jpeg", "png", "webp", "gif", "avif", "svg"):
        ext = "jpg"

    object_key = f"uploads/{user_id}/{int(time.time())}_{uuid.uuid4().hex[:8]}.{ext}"
    content_type = payload.content_type or "image/jpeg"
    expires_in = 3600

    # Check for S3/R2 credentials in environment
    s3_bucket = (
        os.getenv("S3_BUCKET_NAME")
        or os.getenv("R2_BUCKET_NAME")
        or getattr(settings, "S3_BUCKET_NAME", None)
    )
    aws_key = (
        os.getenv("AWS_ACCESS_KEY_ID")
        or os.getenv("R2_ACCESS_KEY_ID")
        or getattr(settings, "AWS_ACCESS_KEY_ID", None)
    )
    aws_secret = (
        os.getenv("AWS_SECRET_ACCESS_KEY")
        or os.getenv("R2_SECRET_ACCESS_KEY")
        or getattr(settings, "AWS_SECRET_ACCESS_KEY", None)
    )

    if s3_bucket and ((aws_key and aws_secret) or os.getenv("AWS_ROLE_ARN") or os.getenv("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI")):
        try:
            upload_url, public_url = generate_s3_presigned_url(
                bucket_name=s3_bucket,
                object_key=object_key,
                content_type=content_type,
                expires_in=expires_in,
            )
            return {
                "upload_url": upload_url,
                "public_url": public_url,
                "object_key": object_key,
                "expires_in": expires_in,
            }
        except NoCredentialsError:
            logger.error("AWS/S3 credentials not found.")
            raise HTTPException(status_code=500, detail="Storage credentials missing.")
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to generate S3 presigned URL: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to generate presigned upload URL: {str(e)}")

    # Development / Offline Direct Local Storage Fallback
    base_url = str(request.base_url).rstrip("/") if request else "http://localhost:8000"
    upload_url = f"{base_url}{settings.API_V1_STR}/uploads/storage/{object_key}"
    public_url = f"{base_url}{settings.API_V1_STR}/uploads/file/{object_key}"

    return {
        "upload_url": upload_url,
        "public_url": public_url,
        "object_key": object_key,
        "expires_in": expires_in,
    }


@router.get("/presigned-url")
async def get_presigned_url(
    filename: str = Query(..., description="File name to upload"),
    content_type: str = Query(default="image/jpeg", description="MIME content type"),
    request: Request = None,
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    GET endpoint for presigned URL generation.
    """
    req = UploadPresignRequest(filename=filename, content_type=content_type)
    return await create_presigned_url(payload=req, request=request, current_user=current_user)


@router.put("/storage/{object_path:path}")
async def upload_binary_storage(object_path: str, request: Request):
    """
    Accepts raw binary PUT upload for local / on-premise cloud storage.
    """
    data = await request.body()
    if not data:
        raise HTTPException(status_code=400, detail="Empty binary payload")

    safe_path = os.path.normpath(object_path).lstrip(os.path.sep).lstrip("/")
    if ".." in safe_path:
        raise HTTPException(status_code=400, detail="Invalid object path")

    file_path = os.path.join(UPLOAD_STORAGE_DIR, safe_path)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(data)

    return {
        "status": "success",
        "object_key": safe_path,
        "bytes_received": len(data),
    }


@router.get("/file/{object_path:path}")
async def serve_uploaded_file(object_path: str):
    """
    Serves stored upload assets for local storage.
    """
    safe_path = os.path.normpath(object_path).lstrip(os.path.sep).lstrip("/")
    if ".." in safe_path:
        raise HTTPException(status_code=400, detail="Invalid object path")

    file_path = os.path.join(UPLOAD_STORAGE_DIR, safe_path)
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Uploaded file not found")

    ext = os.path.splitext(file_path)[1].lower()
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
        ".avif": "image/avif",
        ".svg": "image/svg+xml",
    }
    media_type = media_types.get(ext, "application/octet-stream")
    return FileResponse(file_path, media_type=media_type)
