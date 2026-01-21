from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import base64

from ..services.storage_service import storage_service

router = APIRouter(prefix="/api/storage", tags=["storage"])


class UploadPhotoRequest(BaseModel):
    image_base64: str
    user_id: Optional[str] = "default"
    metadata: Optional[dict] = None


@router.get("/status")
async def get_status():
    """Check if S3 storage is configured."""
    return {
        "configured": storage_service.is_configured(),
        "bucket": storage_service.bucket_name if storage_service.is_configured() else None,
        "region": storage_service.aws_region if storage_service.is_configured() else None
    }


@router.post("/upload/photo")
async def upload_photo(request: UploadPhotoRequest):
    """Upload a photo to S3."""
    return await storage_service.upload_photo(
        image_base64=request.image_base64,
        user_id=request.user_id,
        metadata=request.metadata
    )


@router.post("/upload/photo/file")
async def upload_photo_file(file: UploadFile = File(...), user_id: str = "default"):
    """Upload a photo file to S3."""
    content = await file.read()
    image_base64 = base64.b64encode(content).decode('utf-8')
    return await storage_service.upload_photo(
        image_base64=image_base64,
        user_id=user_id,
        metadata={"original_filename": file.filename}
    )


@router.post("/upload/video/file")
async def upload_video_file(file: UploadFile = File(...), user_id: str = "default"):
    """Upload a video file to S3."""
    content = await file.read()
    return await storage_service.upload_video(
        video_data=content,
        user_id=user_id,
        filename=file.filename,
        metadata={"original_filename": file.filename}
    )


@router.post("/upload/audio/file")
async def upload_audio_file(file: UploadFile = File(...), user_id: str = "default"):
    """Upload an audio file to S3."""
    content = await file.read()
    return await storage_service.upload_audio(
        audio_data=content,
        user_id=user_id,
        filename=file.filename,
        metadata={"original_filename": file.filename}
    )


@router.get("/files")
async def list_files(prefix: str = "", user_id: str = None):
    """List files in S3 bucket."""
    return await storage_service.list_files(prefix=prefix, user_id=user_id)


@router.get("/files/photos/{user_id}")
async def list_user_photos(user_id: str):
    """List photos for a user."""
    return await storage_service.list_files(prefix="photos", user_id=user_id)


@router.get("/files/videos/{user_id}")
async def list_user_videos(user_id: str):
    """List videos for a user."""
    return await storage_service.list_files(prefix="videos", user_id=user_id)


@router.get("/presigned-url")
async def get_presigned_url(key: str, expiration: int = 3600):
    """Get a presigned URL for downloading a file."""
    return await storage_service.get_presigned_url(key, expiration)


@router.delete("/files")
async def delete_file(key: str):
    """Delete a file from S3."""
    return await storage_service.delete_file(key)
