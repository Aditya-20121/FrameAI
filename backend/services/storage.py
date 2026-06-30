"""
Cloudflare R2 storage — S3-compatible via boto3.
All objects are set with a 24-hour TTL via metadata; actual cleanup should be
driven by an R2 lifecycle rule set on the bucket.
"""
import io
from datetime import datetime, timezone, timedelta

import boto3
from botocore.config import Config

from config import settings

PRESIGNED_EXPIRY_SECONDS = 3600  # 1h for client-side access


def _r2() -> boto3.client:
    return boto3.client(
        "s3",
        endpoint_url=f"https://{settings.r2_account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def upload_photo(job_id: str, image_bytes: bytes, content_type: str) -> str:
    """Upload user photo to R2. Returns the R2 object key."""
    key = f"photos/{job_id}.webp"
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()

    _r2().put_object(
        Bucket=settings.r2_bucket_name,
        Key=key,
        Body=image_bytes,
        ContentType=content_type,
        Metadata={"expires_at": expires_at},
    )
    return key


def upload_generated_image(task_id: str, image_bytes: bytes) -> str:
    """Upload a generated portrait image. Returns the R2 object key."""
    key = f"generated/{task_id}.webp"
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()

    _r2().put_object(
        Bucket=settings.r2_bucket_name,
        Key=key,
        Body=image_bytes,
        ContentType="image/webp",
        Metadata={"expires_at": expires_at},
    )
    return key


def get_presigned_url(key: str, expiry: int = PRESIGNED_EXPIRY_SECONDS) -> str:
    """Generate a presigned GET URL for any R2 object."""
    return _r2().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.r2_bucket_name, "Key": key},
        ExpiresIn=expiry,
    )


def download_photo(key: str) -> bytes:
    """Download raw bytes for a stored photo (used by face analysis worker)."""
    response = _r2().get_object(Bucket=settings.r2_bucket_name, Key=key)
    return response["Body"].read()


def download_object(key: str) -> bytes:
    """Download any R2 object by key."""
    response = _r2().get_object(Bucket=settings.r2_bucket_name, Key=key)
    return response["Body"].read()


def r2_key_from_url(url: str) -> str | None:
    """
    Extract the R2 object key from a public URL.
    e.g. 'https://r2.frameai.in/frames/abc.webp' → 'frames/abc.webp'
    Returns None if the URL is not an R2 URL.
    """
    domain = settings.r2_public_domain.rstrip("/")
    if url.startswith(domain):
        return url[len(domain):].lstrip("/")
    return None


def upload_temp_and_presign(key: str, image_bytes: bytes, content_type: str = "image/jpeg") -> str:
    """Upload bytes to R2 and return a 1-hour presigned GET URL (used to pass images to external APIs)."""
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    _r2().put_object(
        Bucket=settings.r2_bucket_name,
        Key=key,
        Body=image_bytes,
        ContentType=content_type,
        Metadata={"expires_at": expires_at},
    )
    return get_presigned_url(key, expiry=3600)


def delete_object(key: str) -> None:
    """Delete a single R2 object by key."""
    _r2().delete_object(Bucket=settings.r2_bucket_name, Key=key)


def public_url(key: str) -> str:
    """Return the public CDN URL for a permanent frame catalogue image."""
    return f"{settings.r2_public_domain}/{key}"
