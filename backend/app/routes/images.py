import logging

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from starlette.concurrency import run_in_threadpool
from app.config import settings
from app.services.file_storage import FileStorageService, PersistentFileStoreUnavailable
from app.services.mongodb_service import mongodb_service

router = APIRouter(prefix="/api/images", tags=["Images"])
logger = logging.getLogger(__name__)

@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """
    Validates format, magic bytes, dimensions, and saves image with safe UUID.
    """
    try:
        result = await run_in_threadpool(
            FileStorageService.validate_and_save_image_stream,
            source=file.file,
            original_filename=file.filename or "upload.jpg",
            content_type=file.content_type or "image/jpeg"
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except PersistentFileStoreUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as e:
        logger.exception("Failed to process uploaded image '%s'", file.filename)
        raise HTTPException(status_code=500, detail="Failed to process image upload.")
    finally:
        await file.close()

@router.get("/{image_id}/preview")
def preview_image(image_id: str):
    """
    Safely serves preview of an uploaded image without directory traversal.
    """
    img_path = FileStorageService.get_image_path(image_id)
    if not img_path or not img_path.is_file():
        if settings.REQUIRE_PERSISTENT_JOB_STORE and (
            not settings.MONGODB_URI or not settings.MONGODB_GRIDFS_ENABLED
        ):
            raise HTTPException(
                status_code=503,
                detail="Persistent image storage is misconfigured; configure MongoDB and GridFS to retrieve this image.",
            )
        if settings.MONGODB_URI and not mongodb_service.is_connected():
            raise HTTPException(
                status_code=503,
                detail="MongoDB is temporarily unavailable; the uploaded image could not be retrieved from persistent storage.",
            )
        if settings.REQUIRE_PERSISTENT_JOB_STORE and not mongodb_service.is_gridfs_available():
            raise HTTPException(
                status_code=503,
                detail="MongoDB GridFS is unavailable; the uploaded image could not be retrieved from persistent storage.",
            )
        raise HTTPException(status_code=404, detail="Image not found.")
    
    media_type = "image/jpeg"
    if img_path.suffix.lower() == ".png":
        media_type = "image/png"
    elif img_path.suffix.lower() == ".webp":
        media_type = "image/webp"

    return FileResponse(img_path, media_type=media_type)
