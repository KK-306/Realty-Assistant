from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from typing import List
from app.services.file_storage import FileStorageService

router = APIRouter(prefix="/api/images", tags=["Images"])

@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """
    Validates format, magic bytes, dimensions, and saves image with safe UUID.
    """
    try:
        content = await file.read()
        result = FileStorageService.validate_and_save_image(
            file_bytes=content,
            original_filename=file.filename or "upload.jpg",
            content_type=file.content_type or "image/jpeg"
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to process image upload.")

@router.get("/{image_id}/preview")
def preview_image(image_id: str):
    """
    Safely serves preview of an uploaded image without directory traversal.
    """
    img_path = FileStorageService.get_image_path(image_id)
    if not img_path or not img_path.is_file():
        raise HTTPException(status_code=404, detail="Image not found.")
    
    media_type = "image/jpeg"
    if img_path.suffix.lower() == ".png":
        media_type = "image/png"
    elif img_path.suffix.lower() == ".webp":
        media_type = "image/webp"

    return FileResponse(img_path, media_type=media_type)
