"""
UrivDocs — storage_s3.py
Handles file uploads to AWS S3.
If S3 is not configured, falls back to local storage.
"""
from __future__ import annotations
import os
from pathlib import Path
from loguru import logger

# S3 config from environment variables
S3_BUCKET      = os.getenv("S3_BUCKET", "")
S3_REGION      = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")

USE_S3 = bool(S3_BUCKET and AWS_ACCESS_KEY and AWS_SECRET_KEY)


def get_s3_client():
    """Get boto3 S3 client."""
    import boto3
    return boto3.client(
        "s3",
        region_name=S3_REGION,
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
    )


def upload_to_s3(local_path: Path, filename: str) -> str:
    """
    Upload a file to S3.
    Returns the S3 URL of the uploaded file.
    """
    if not USE_S3:
        logger.info("S3 not configured — using local storage")
        return ""
    try:
        s3 = get_s3_client()
        s3_key = f"uploads/{filename}"
        s3.upload_file(
            str(local_path),
            S3_BUCKET,
            s3_key,
            ExtraArgs={"ContentType": "application/octet-stream"},
        )
        url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{s3_key}"
        logger.info(f"✅ Uploaded to S3: {url}")
        return url
    except Exception as e:
        logger.error(f"S3 upload failed: {e}")
        return ""


def download_from_s3(filename: str, local_path: Path) -> bool:
    """Download a file from S3 to local path."""
    if not USE_S3:
        return False
    try:
        s3 = get_s3_client()
        s3_key = f"uploads/{filename}"
        s3.download_file(S3_BUCKET, s3_key, str(local_path))
        logger.info(f"✅ Downloaded from S3: {filename}")
        return True
    except Exception as e:
        logger.error(f"S3 download failed: {e}")
        return False


def delete_from_s3(filename: str) -> bool:
    """Delete a file from S3."""
    if not USE_S3:
        return False
    try:
        s3 = get_s3_client()
        s3_key = f"uploads/{filename}"
        s3.delete_object(Bucket=S3_BUCKET, Key=s3_key)
        logger.info(f"✅ Deleted from S3: {filename}")
        return True
    except Exception as e:
        logger.error(f"S3 delete failed: {e}")
        return False


def list_s3_files() -> list:
    """List all uploaded files in S3 bucket."""
    if not USE_S3:
        return []
    try:
        s3 = get_s3_client()
        response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix="uploads/")
        files = []
        for obj in response.get("Contents", []):
            key = obj["Key"]
            name = key.replace("uploads/", "")
            if name:
                files.append({
                    "filename": name,
                    "size": obj["Size"],
                    "last_modified": str(obj["LastModified"]),
                })
        return files
    except Exception as e:
        logger.error(f"S3 list failed: {e}")
        return []
