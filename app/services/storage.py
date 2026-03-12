"""S3-compatible object storage service (works with MinIO for local dev)."""

from __future__ import annotations

import logging
from typing import BinaryIO

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Thin wrapper around boto3 S3 client for file upload/download/delete."""

    def __init__(self) -> None:
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name="us-east-1",
        )
        self._bucket = settings.S3_BUCKET
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        """Create the bucket if it doesn't already exist."""
        try:
            self._client.head_bucket(Bucket=self._bucket)
        except ClientError:
            try:
                self._client.create_bucket(Bucket=self._bucket)
                logger.info("Created S3 bucket: %s", self._bucket)
            except ClientError:
                logger.exception("Failed to create S3 bucket: %s", self._bucket)
                raise

    def upload_file(self, file_obj: BinaryIO, key: str, content_type: str = "application/octet-stream") -> str:
        """Upload a file object to S3. Returns the key."""
        self._client.upload_fileobj(
            file_obj,
            self._bucket,
            key,
            ExtraArgs={"ContentType": content_type},
        )
        return key

    def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """Generate a presigned download URL (default 1 hour expiry)."""
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    def delete_file(self, key: str) -> None:
        """Delete an object from S3."""
        self._client.delete_object(Bucket=self._bucket, Key=key)


# Module-level singleton (lazy)
_storage: StorageService | None = None


def get_storage() -> StorageService:
    """Return a singleton StorageService instance."""
    global _storage  # noqa: PLW0603
    if _storage is None:
        _storage = StorageService()
    return _storage
