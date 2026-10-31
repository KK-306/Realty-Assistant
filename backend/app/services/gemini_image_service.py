import base64
import logging
from typing import Tuple

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class GeminiImageService:
    """Generate illustrative real-estate visuals through Gemini's image API."""

    @classmethod
    def is_available(cls) -> bool:
        return settings.LLM_PROVIDER == "gemini" and bool(settings.LLM_API_KEY)

    @classmethod
    def generate_concept_image(cls, prompt: str, aspect_ratio: str) -> Tuple[bytes, str]:
        if not cls.is_available():
            raise ValueError(
                "Upload at least 4 photos, or configure LLM_PROVIDER=gemini and LLM_API_KEY to generate the missing scene images."
            )

        url = "https://generativelanguage.googleapis.com/v1beta/interactions"
        payload = {
            "model": settings.GEMINI_IMAGE_MODEL,
            "input": prompt,
            "response_format": {
                "type": "image",
                "aspect_ratio": aspect_ratio,
                "image_size": "1K",
            },
        }

        try:
            with httpx.Client(timeout=150.0) as client:
                response = client.post(
                    url,
                    json=payload,
                    headers={"x-goog-api-key": settings.LLM_API_KEY},
                )
            if response.status_code >= 400:
                logger.warning("Gemini image request failed with HTTP %s", response.status_code)
                raise RuntimeError(
                    f"Gemini could not generate a missing scene image (HTTP {response.status_code}). Check the API key, image model, and quota."
                )

            data = response.json()
            image_block = cls._find_image_block(data)
            if not image_block or not image_block.get("data"):
                raise RuntimeError("Gemini returned no image for a requested scene.")

            image_bytes = base64.b64decode(image_block["data"], validate=True)
            content_type = image_block.get("mime_type") or image_block.get("mimeType") or "image/png"
            if content_type not in ("image/jpeg", "image/png", "image/webp"):
                raise RuntimeError("Gemini returned an unsupported image format.")
            return image_bytes, content_type
        except httpx.TimeoutException as exc:
            raise RuntimeError("Gemini image generation timed out. Please retry or upload more photos.") from exc
        except httpx.RequestError as exc:
            raise RuntimeError("Could not connect to Gemini image generation. Check the server's internet connection.") from exc
        except (ValueError, KeyError, TypeError) as exc:
            raise RuntimeError("Gemini returned an invalid image response. Please retry.") from exc

    @staticmethod
    def _find_image_block(data: dict):
        for step in data.get("steps", []):
            if step.get("type") != "model_output":
                continue
            for block in step.get("content", []):
                if block.get("type") == "image":
                    return block

        # Some API responses expose a convenience output field as well.
        output_image = data.get("output_image")
        if isinstance(output_image, dict):
            return output_image
        return None
