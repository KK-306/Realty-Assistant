import os
import uuid
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from PIL import Image

from app.config import settings, UPLOAD_DIR, OUTPUT_DIR, SAMPLE_DIR
from app.services.mongodb_service import mongodb_service

class FileStorageService:
    @staticmethod
    def is_allowed_mime(content_type: str) -> bool:
        return content_type.lower() in settings.ALLOWED_IMAGE_TYPES

    @classmethod
    def validate_and_save_image(cls, file_bytes: bytes, original_filename: str, content_type: str) -> Dict[str, Any]:
        """
        Validates image content using PIL to guard against corrupted files,
        file spoofing, and excessive dimensions, then saves with a secure UUID.
        """
        # Size validation
        size_mb = len(file_bytes) / (1024 * 1024)
        if size_mb > settings.MAX_FILE_SIZE_MB:
            raise ValueError(f"File size ({size_mb:.1f}MB) exceeds maximum allowed limit of {settings.MAX_FILE_SIZE_MB}MB.")

        if not cls.is_allowed_mime(content_type):
            raise ValueError(f"Unsupported image MIME type: {content_type}. Only JPEG, PNG, and WebP are supported.")

        # Content validation with PIL (verifies actual image integrity and dimensions)
        import io
        try:
            with Image.open(io.BytesIO(file_bytes)) as img:
                img.verify()  # Verifies image integrity
            # Reopen to read metadata (verify closes the image)
            with Image.open(io.BytesIO(file_bytes)) as img:
                width, height = img.size
                image_format = (img.format or "JPEG").lower()
                if image_format == "jpeg":
                    ext = ".jpg"
                elif image_format == "png":
                    ext = ".png"
                elif image_format == "webp":
                    ext = ".webp"
                else:
                    ext = ".jpg"
                    
                if width < 300 or height < 300:
                    raise ValueError(f"Image resolution {width}x{height} is too small. Minimum resolution is 300x300.")
        except Exception as e:
            if "Image resolution" in str(e) or "File size" in str(e) or "Unsupported" in str(e):
                raise
            raise ValueError("Uploaded file is corrupted or not a valid image.")

        # Generate safe unique ID and path
        image_id = str(uuid.uuid4())
        safe_filename = f"{image_id}{ext}"
        destination_path = UPLOAD_DIR / safe_filename

        with open(destination_path, "wb") as f:
            f.write(file_bytes)

        # Also persist to MongoDB GridFS if connected
        gridfs_id = None
        if mongodb_service.is_connected() and settings.MONGODB_GRIDFS_ENABLED:
            gridfs_id = mongodb_service.save_file_to_gridfs(
                file_bytes=file_bytes,
                filename=safe_filename,
                content_type=content_type,
                metadata={
                    "image_id": image_id,
                    "original_filename": original_filename,
                    "width": width,
                    "height": height
                }
            )

        return {
            "image_id": image_id,
            "filename": safe_filename,
            "original_filename": original_filename,
            "width": width,
            "height": height,
            "size_bytes": len(file_bytes),
            "preview_url": f"/api/images/{image_id}/preview",
            "gridfs_id": gridfs_id
        }

    @classmethod
    def get_image_path(cls, image_id: str) -> Optional[Path]:
        """
        Returns the absolute Path of an image by image_id, preventing directory traversal.
        If file is missing locally but stored in MongoDB GridFS, it recovers/caches it locally.
        """
        safe_id = Path(image_id).name
        # Check standard upload extensions on local disk
        for ext in [".jpg", ".jpeg", ".png", ".webp"]:
            candidate = UPLOAD_DIR / f"{safe_id}{ext}"
            if candidate.is_file():
                return candidate
                
        # Also check if it refers to a sample image
        sample_file = SAMPLE_DIR / safe_id
        if sample_file.is_file():
            return sample_file

        # Check if stored in MongoDB GridFS
        if mongodb_service.is_connected() and settings.MONGODB_GRIDFS_ENABLED:
            for ext in [".jpg", ".jpeg", ".png", ".webp", ""]:
                test_filename = f"{safe_id}{ext}" if not safe_id.endswith(ext) else safe_id
                data = mongodb_service.get_file_from_gridfs(test_filename)
                if data:
                    ext_to_use = ext or ".jpg"
                    recovered_path = UPLOAD_DIR / f"{safe_id}{ext_to_use}"
                    with open(recovered_path, "wb") as f:
                        f.write(data)
                    return recovered_path
            
        return None

    @classmethod
    def get_sample_images(cls) -> list[Dict[str, Any]]:
        """
        Returns metadata for pre-bundled demonstration images.
        """
        sample_files = sorted(SAMPLE_DIR.glob("*.jpg"))
        results = []
        for sf in sample_files:
            try:
                with Image.open(sf) as img:
                    w, h = img.size
                results.append({
                    "image_id": sf.name,
                    "filename": sf.name,
                    "original_filename": sf.stem.replace("_", " ").title() + ".jpg",
                    "width": w,
                    "height": h,
                    "size_bytes": sf.stat().st_size,
                    "preview_url": f"/api/samples/images/{sf.name}"
                })
            except Exception:
                continue
        return results

    @classmethod
    def get_video_path(cls, video_id: str) -> Optional[Path]:
        safe_id = Path(video_id).name
        candidate = OUTPUT_DIR / f"{safe_id}.mp4"
        if candidate.is_file():
            return candidate

        # Check if stored in MongoDB GridFS
        if mongodb_service.is_connected() and settings.MONGODB_GRIDFS_ENABLED:
            video_filename = f"{safe_id}.mp4"
            data = mongodb_service.get_file_from_gridfs(video_filename)
            if data:
                with open(candidate, "wb") as f:
                    f.write(data)
                return candidate

        return None
