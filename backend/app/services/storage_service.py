"""
Storage Service - AWS S3 integration for photos and videos.
"""

import asyncio
import base64
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
from typing import Optional
from pathlib import Path
import uuid

from ..config import get_settings

settings = get_settings()


class StorageService:
    def __init__(self):
        self.aws_access_key = getattr(settings, 'aws_access_key_id', '') or ''
        self.aws_secret_key = getattr(settings, 'aws_secret_access_key', '') or ''
        self.aws_region = getattr(settings, 'aws_region', 'us-east-1') or 'us-east-1'
        self.bucket_name = getattr(settings, 'aws_s3_bucket', '') or ''
        self.enabled = bool(self.aws_access_key and self.aws_secret_key and self.bucket_name)
        self._client = None

    def _get_client(self):
        """Get or create S3 client."""
        if self._client is None and self.enabled:
            self._client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region
            )
        return self._client

    def is_configured(self) -> bool:
        return self.enabled

    async def upload_photo(self, image_base64: str, user_id: str = "default",
                          metadata: Optional[dict] = None) -> dict:
        """Upload a photo to S3."""
        if not self.enabled:
            return {"success": False, "message": "S3 not configured"}

        try:
            client = self._get_client()

            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_id = str(uuid.uuid4())[:8]
            key = f"photos/{user_id}/{timestamp}_{file_id}.jpg"

            # Decode base64 image
            image_data = base64.b64decode(image_base64)

            # Prepare metadata
            s3_metadata = {
                "user_id": user_id,
                "uploaded_at": datetime.now().isoformat(),
                "content_type": "image/jpeg"
            }
            if metadata:
                s3_metadata.update({k: str(v) for k, v in metadata.items()})

            # Upload to S3
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=image_data,
                    ContentType="image/jpeg",
                    Metadata=s3_metadata
                )
            )

            # Generate URL
            url = f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{key}"

            return {
                "success": True,
                "key": key,
                "url": url,
                "message": "Photo uploaded successfully"
            }

        except ClientError as e:
            return {"success": False, "message": f"S3 error: {str(e)}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    async def upload_video(self, video_data: bytes, user_id: str = "default",
                          filename: str = None, metadata: Optional[dict] = None) -> dict:
        """Upload a video to S3."""
        if not self.enabled:
            return {"success": False, "message": "S3 not configured"}

        try:
            client = self._get_client()

            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_id = str(uuid.uuid4())[:8]
            ext = Path(filename).suffix if filename else ".mp4"
            key = f"videos/{user_id}/{timestamp}_{file_id}{ext}"

            # Determine content type
            content_type = "video/mp4"
            if ext == ".webm":
                content_type = "video/webm"
            elif ext == ".mov":
                content_type = "video/quicktime"

            # Prepare metadata
            s3_metadata = {
                "user_id": user_id,
                "uploaded_at": datetime.now().isoformat(),
                "content_type": content_type
            }
            if metadata:
                s3_metadata.update({k: str(v) for k, v in metadata.items()})

            # Upload to S3
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=video_data,
                    ContentType=content_type,
                    Metadata=s3_metadata
                )
            )

            # Generate URL
            url = f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{key}"

            return {
                "success": True,
                "key": key,
                "url": url,
                "message": "Video uploaded successfully"
            }

        except ClientError as e:
            return {"success": False, "message": f"S3 error: {str(e)}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    async def upload_audio(self, audio_data: bytes, user_id: str = "default",
                          filename: str = None, metadata: Optional[dict] = None) -> dict:
        """Upload audio to S3."""
        if not self.enabled:
            return {"success": False, "message": "S3 not configured"}

        try:
            client = self._get_client()

            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_id = str(uuid.uuid4())[:8]
            ext = Path(filename).suffix if filename else ".mp3"
            key = f"audio/{user_id}/{timestamp}_{file_id}{ext}"

            content_type = "audio/mpeg" if ext == ".mp3" else "audio/wav"

            # Prepare metadata
            s3_metadata = {
                "user_id": user_id,
                "uploaded_at": datetime.now().isoformat()
            }
            if metadata:
                s3_metadata.update({k: str(v) for k, v in metadata.items()})

            # Upload to S3
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=audio_data,
                    ContentType=content_type,
                    Metadata=s3_metadata
                )
            )

            url = f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{key}"

            return {
                "success": True,
                "key": key,
                "url": url,
                "message": "Audio uploaded successfully"
            }

        except Exception as e:
            return {"success": False, "message": str(e)}

    async def get_presigned_url(self, key: str, expiration: int = 3600) -> dict:
        """Generate a presigned URL for downloading."""
        if not self.enabled:
            return {"success": False, "message": "S3 not configured"}

        try:
            client = self._get_client()
            loop = asyncio.get_event_loop()

            url = await loop.run_in_executor(
                None,
                lambda: client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': key},
                    ExpiresIn=expiration
                )
            )

            return {"success": True, "url": url, "expires_in": expiration}

        except Exception as e:
            return {"success": False, "message": str(e)}

    async def list_files(self, prefix: str = "", user_id: str = None) -> dict:
        """List files in S3 bucket."""
        if not self.enabled:
            return {"success": False, "message": "S3 not configured"}

        try:
            client = self._get_client()

            if user_id:
                prefix = f"{prefix}/{user_id}" if prefix else user_id

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=prefix,
                    MaxKeys=100
                )
            )

            files = []
            for obj in response.get('Contents', []):
                files.append({
                    "key": obj['Key'],
                    "size": obj['Size'],
                    "last_modified": obj['LastModified'].isoformat(),
                    "url": f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{obj['Key']}"
                })

            return {
                "success": True,
                "count": len(files),
                "files": files
            }

        except Exception as e:
            return {"success": False, "message": str(e)}

    async def delete_file(self, key: str) -> dict:
        """Delete a file from S3."""
        if not self.enabled:
            return {"success": False, "message": "S3 not configured"}

        try:
            client = self._get_client()
            loop = asyncio.get_event_loop()

            await loop.run_in_executor(
                None,
                lambda: client.delete_object(Bucket=self.bucket_name, Key=key)
            )

            return {"success": True, "message": f"Deleted {key}"}

        except Exception as e:
            return {"success": False, "message": str(e)}


# Singleton instance
storage_service = StorageService()
