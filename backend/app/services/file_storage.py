import io
import logging
import uuid
from pathlib import Path
from threading import Lock
from typing import Any, BinaryIO, Dict, Optional

from PIL import Image, ImageOps

from app.config import OUTPUT_DIR, SAMPLE_DIR, UPLOAD_DIR, settings
from app.services.mongodb_service import mongodb_service

logger = logging.getLogger(__name__)
_SAMPLE_IMAGE_NAMES = (
    "1_exterior_facade.jpg",
    "2_living_room.jpg",
    "3_modular_kitchen.jpg",
    "4_master_bedroom.jpg",
    "5_private_balcony.jpg",
    "6_covered_parking.jpg",
)
_SAMPLE_IMAGE_LOCK = Lock()
_IMAGE_PROCESSING_LOCK = Lock()


class PersistentFileStoreUnavailable(RuntimeError):
    """Raised when the deployment requires an image to exist in GridFS."""


class FileStorageService:
    @staticmethod
    def is_allowed_mime(content_type: str) -> bool:
        return content_type.lower() in settings.ALLOWED_IMAGE_TYPES

    @classmethod
    def validate_and_save_image(cls, file_bytes: bytes, original_filename: str, content_type: str) -> Dict[str, Any]:
        """Compatibility wrapper for callers that already hold image bytes."""
        return cls.validate_and_save_image_stream(io.BytesIO(file_bytes), original_filename, content_type)

    @classmethod
    def validate_and_save_image_stream(
        cls,
        source: BinaryIO,
        original_filename: str,
        content_type: str,
        chunk_size: int = 1024 * 1024,
    ) -> Dict[str, Any]:
        """Stage, validate, resize and compress an upload without buffering it in RAM."""
        if not cls.is_allowed_mime(content_type):
            raise ValueError(f"Unsupported image MIME type: {content_type}. Only JPEG, PNG, and WebP are supported.")

        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        staged_path = UPLOAD_DIR / f".upload-{uuid.uuid4().hex}.tmp"
        image_id = str(uuid.uuid4())
        destination_path = UPLOAD_DIR / f"{image_id}.jpg"
        source_size = 0
        width = height = 0

        try:
            with staged_path.open("wb") as staged:
                while chunk := source.read(chunk_size):
                    source_size += len(chunk)
                    if source_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
                        size_mb = source_size / (1024 * 1024)
                        raise ValueError(
                            f"File size ({size_mb:.1f}MB) exceeds maximum allowed limit of "
                            f"{settings.MAX_FILE_SIZE_MB}MB."
                        )
                    staged.write(chunk)

            with _IMAGE_PROCESSING_LOCK:
                with Image.open(staged_path) as image:
                    width, height = image.size
                    image_format = (image.format or "").upper()
                    if image_format not in {"JPEG", "PNG", "WEBP"}:
                        raise ValueError("Uploaded file is corrupted or not a supported JPEG, PNG, or WebP image.")
                    if width < 300 or height < 300:
                        raise ValueError(f"Image resolution {width}x{height} is too small. Minimum resolution is 300x300.")
                    if width * height > settings.MAX_UPLOAD_IMAGE_PIXELS:
                        raise ValueError(
                            f"Image dimensions {width}x{height} exceed the maximum supported pixel count "
                            f"({settings.MAX_UPLOAD_IMAGE_PIXELS:,})."
                        )
                    image.verify()

                with Image.open(staged_path) as source_image:
                    oriented = ImageOps.exif_transpose(source_image)
                    try:
                        oriented.thumbnail(
                            (settings.MAX_UPLOAD_IMAGE_EDGE, settings.MAX_UPLOAD_IMAGE_EDGE),
                            Image.Resampling.LANCZOS,
                        )
                        if "A" in oriented.getbands() or "transparency" in oriented.info:
                            rgba = oriented.convert("RGBA")
                            alpha = rgba.getchannel("A")
                            normalized = Image.new("RGB", rgba.size, (255, 255, 255))
                            try:
                                normalized.paste(rgba, mask=alpha)
                            finally:
                                alpha.close()
                                rgba.close()
                        else:
                            normalized = oriented.convert("RGB")
                        try:
                            normalized.save(
                                destination_path,
                                format="JPEG",
                                quality=settings.UPLOAD_IMAGE_JPEG_QUALITY,
                                optimize=False,
                                progressive=False,
                            )
                        finally:
                            normalized.close()
                    finally:
                        if oriented is not source_image:
                            oriented.close()
        except ValueError:
            destination_path.unlink(missing_ok=True)
            raise
        except Exception as exc:
            destination_path.unlink(missing_ok=True)
            if "DecompressionBomb" in type(exc).__name__:
                raise ValueError("Image dimensions are too large to process safely.") from exc
            raise ValueError("Uploaded file is corrupted or not a valid image.") from exc
        finally:
            staged_path.unlink(missing_ok=True)

        if not destination_path.is_file() or destination_path.stat().st_size == 0:
            raise ValueError("The uploaded image could not be normalized for rendering.")

        safe_filename = destination_path.name
        stored_size = destination_path.stat().st_size
        logger.info(
            "Normalized uploaded image %s: %sx%s source_bytes=%s stored_bytes=%s",
            image_id, width, height, source_size, stored_size,
        )
        gridfs_id = None
        if mongodb_service.is_connected() and settings.MONGODB_GRIDFS_ENABLED:
            gridfs_id = mongodb_service.save_path_to_gridfs(
                file_path=destination_path,
                filename=safe_filename,
                content_type="image/jpeg",
                metadata={
                    "image_id": image_id,
                    "original_filename": original_filename,
                    "width": width,
                    "height": height,
                    "stored_size_bytes": stored_size,
                },
            )
        if settings.REQUIRE_PERSISTENT_JOB_STORE and not gridfs_id:
            destination_path.unlink(missing_ok=True)
            raise PersistentFileStoreUnavailable(
                "The image could not be stored in MongoDB GridFS, which is required by this deployment."
            )

        return {
            "image_id": image_id,
            "filename": safe_filename,
            "original_filename": original_filename,
            "width": width,
            "height": height,
            "size_bytes": source_size,
            "stored_size_bytes": stored_size,
            "preview_url": f"/api/images/{image_id}/preview",
            "gridfs_id": gridfs_id,
        }

    @classmethod
    def _restore_gridfs_file(cls, filename: str, destination: Path) -> bool:
        temporary_path = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.part")
        try:
            if not mongodb_service.copy_file_from_gridfs(filename, temporary_path):
                return False
            temporary_path.replace(destination)
            return True
        finally:
            temporary_path.unlink(missing_ok=True)

    @classmethod
    def get_image_path(cls, image_id: str) -> Optional[Path]:
        """Resolve an uploaded, sample, or GridFS-backed image without a byte buffer."""
        safe_id = Path(image_id).name
        for ext in (".jpg", ".jpeg", ".png", ".webp"):
            candidate = UPLOAD_DIR / f"{safe_id}{ext}"
            if candidate.is_file():
                return candidate

        sample_file = SAMPLE_DIR / safe_id
        if sample_file.is_file():
            return sample_file

        if mongodb_service.is_connected() and settings.MONGODB_GRIDFS_ENABLED:
            filenames = [safe_id] if Path(safe_id).suffix else [f"{safe_id}{ext}" for ext in (".jpg", ".jpeg", ".png", ".webp")]
            for filename in filenames:
                ext = Path(filename).suffix or ".jpg"
                recovered_path = UPLOAD_DIR / f"{Path(filename).stem}{ext}"
                if cls._restore_gridfs_file(filename, recovered_path):
                    return recovered_path
        return None

    @classmethod
    def get_sample_images(cls) -> list[Dict[str, Any]]:
        """Return metadata for pre-bundled demonstration images."""
        cls.ensure_sample_images()
        results = []
        for sample_file in sorted(SAMPLE_DIR.glob("*.jpg")):
            try:
                with Image.open(sample_file) as image:
                    width, height = image.size
                results.append({
                    "image_id": sample_file.name,
                    "filename": sample_file.name,
                    "original_filename": sample_file.stem.replace("_", " ").title() + ".jpg",
                    "width": width,
                    "height": height,
                    "size_bytes": sample_file.stat().st_size,
                    "preview_url": f"/sample-properties/{sample_file.name}",
                })
            except Exception:
                logger.warning("Could not read sample image metadata for %s", sample_file, exc_info=True)
        return results

    @classmethod
    def ensure_sample_images(cls) -> None:
        """Regenerate bundled demo images if a deployment omitted the binaries."""
        if all((SAMPLE_DIR / name).is_file() for name in _SAMPLE_IMAGE_NAMES):
            return

        with _SAMPLE_IMAGE_LOCK:
            if all((SAMPLE_DIR / name).is_file() for name in _SAMPLE_IMAGE_NAMES):
                return
            try:
                from app.assets.generate_assets import generate_sample_images

                logger.warning("Demo images are missing; generating sample images on this instance.")
                generate_sample_images()
            except Exception:
                logger.exception("Could not generate missing demo images.")

    @classmethod
    def get_video_path(cls, video_id: str) -> Optional[Path]:
        safe_id = Path(video_id).name
        candidate = OUTPUT_DIR / f"{safe_id}.mp4"
        if candidate.is_file():
            return candidate

        if mongodb_service.is_connected() and settings.MONGODB_GRIDFS_ENABLED:
            if cls._restore_gridfs_file(f"{safe_id}.mp4", candidate):
                return candidate
        return None
