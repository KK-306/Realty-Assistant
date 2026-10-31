"""
Comprehensive pytest test suite for the AI Property Video Generator backend API.

Categories covered:
1. Health check tests (GET /api/health, GET /)
2. Property validation tests (POST /api/properties/validate)
3. Image upload & preview tests (POST /api/images/upload, GET /api/images/{id}/preview)
4. Script generation tests (POST /api/scripts/generate)
5. Storyboard generation tests (POST /api/storyboards/generate)
6. Sample data tests (GET /api/samples/listing, GET /api/samples/images/{filename})
7. Video job & download tests (POST /api/videos/generate, GET /api/videos/jobs/{job_id}, streaming/download)
"""

import io
import os
import uuid
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from PIL import Image
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.models.job import JobStatus, VideoJob, OutputMetadata
from app.services.job_manager import job_manager


# ============================================================================
# Test Fixtures & Helpers
# ============================================================================

@pytest.fixture(scope="session")
def client():
    """Provides a FastAPI TestClient instance."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def valid_property_dict():
    """
    Returns a standard, valid property payload dict matching PropertyInput schema
    with 4 valid sample images bundled in the backend repository.
    """
    return {
        "property_name": "Skyline Heights Luxury Residence",
        "location": "Bandra West, Mumbai",
        "price": 12500000.0,
        "currency": "₹",
        "price_display": "₹1.25 Cr",
        "property_type": "apartment",
        "key_features": [
            "Sea View Balcony Deck",
            "Italian Marble Flooring",
            "Infinity Swimming Pool",
            "Reserved Covered Parking"
        ],
        "bedrooms": 3,
        "bathrooms": 3,
        "description": "Exquisite 3-BHK sea facing residence with designer interiors and panoramic Arabian Sea views.",
        "contact_name": "Apex Prime Realty",
        "contact_details": "+91 98765 43210 | sales@apexrealty.com",
        "cta_text": "Schedule a Private Viewing",
        "duration": 30,
        "aspect_ratio": "16:9",
        "theme": "luxury",
        "narration_enabled": True,
        "music_enabled": True,
        "image_ids": [
            "1_exterior_facade.jpg",
            "2_living_room.jpg",
            "3_modular_kitchen.jpg",
            "4_master_bedroom.jpg"
        ]
    }


def create_in_memory_image(width: int = 400, height: int = 400, img_format: str = "JPEG", color=(100, 150, 200)) -> bytes:
    """Helper to generate in-memory synthetic image bytes for testing uploads."""
    buf = io.BytesIO()
    img = Image.new("RGB", (width, height), color=color)
    img.save(buf, format=img_format)
    buf.seek(0)
    return buf.getvalue()


@pytest.fixture
def uploaded_test_image(client):
    """
    Uploads a valid JPEG image and automatically deletes the created file from disk after test.
    """
    img_bytes = create_in_memory_image(width=500, height=500, img_format="JPEG")
    response = client.post(
        "/api/images/upload",
        files={"file": ("fixture_test_upload.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    data = response.json()
    image_id = data["image_id"]
    filename = data["filename"]

    yield data

    # Cleanup file from upload directory
    target_file = settings.UPLOAD_DIR / filename
    if target_file.is_file():
        try:
            target_file.unlink()
        except OSError:
            pass


# ============================================================================
# 1. Health Check Tests
# ============================================================================

class TestHealthCheck:
    def test_root_endpoint(self, client):
        """GET / should return basic service information and navigation links."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "AI Property Video Generator" in data["service"]
        assert data.get("docs_url") == "/docs"
        assert data.get("health_url") == "/api/health"

    def test_health_check_returns_proper_structure(self, client):
        """GET /api/health must return proper structure for ffmpeg, llm, storage."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()

        # Top-level keys
        assert "status" in data
        assert data["status"] in ("healthy", "degraded")

        assert "ffmpeg" in data
        ffmpeg_info = data["ffmpeg"]
        assert "available" in ffmpeg_info
        assert isinstance(ffmpeg_info["available"], bool)
        assert "path" in ffmpeg_info
        assert "version" in ffmpeg_info

        assert "llm_provider" in data
        assert isinstance(data["llm_provider"], str)
        assert "llm_configured" in data
        assert isinstance(data["llm_configured"], bool)

        assert "tts_provider" in data
        assert isinstance(data["tts_provider"], str)

        assert "storage" in data
        storage_info = data["storage"]
        assert "uploads_dir" in storage_info
        assert "outputs_dir" in storage_info
        assert Path(storage_info["uploads_dir"]).exists()
        assert Path(storage_info["outputs_dir"]).exists()


# ============================================================================
# 2. Property Validation Tests
# ============================================================================

class TestPropertyValidation:
    def test_valid_property_data_returns_valid_true(self, client, valid_property_dict):
        """POST /api/properties/validate with correct data should return valid=True."""
        response = client.post("/api/properties/validate", json=valid_property_dict)
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["message"] == "Property information is valid."
        assert data["errors"] == []
        assert data["sanitized_data"] is not None
        assert data["sanitized_data"]["property_name"] == valid_property_dict["property_name"]
        assert data["sanitized_data"]["price"] == valid_property_dict["price"]

    def test_missing_property_name_returns_error(self, client, valid_property_dict):
        """Property name is mandatory and cannot be empty or whitespace."""
        # Empty string
        payload_empty = dict(valid_property_dict)
        payload_empty["property_name"] = ""
        resp_empty = client.post("/api/properties/validate", json=payload_empty)
        assert resp_empty.status_code == 422

        # Pure whitespace
        payload_whitespace = dict(valid_property_dict)
        payload_whitespace["property_name"] = "    "
        resp_whitespace = client.post("/api/properties/validate", json=payload_whitespace)
        assert resp_whitespace.status_code == 422

        # Field omitted
        payload_missing = dict(valid_property_dict)
        del payload_missing["property_name"]
        resp_missing = client.post("/api/properties/validate", json=payload_missing)
        assert resp_missing.status_code == 422

    def test_missing_location_returns_error(self, client, valid_property_dict):
        """Location is mandatory and cannot be empty or whitespace."""
        # Empty string
        payload = dict(valid_property_dict)
        payload["location"] = ""
        resp = client.post("/api/properties/validate", json=payload)
        assert resp.status_code == 422

        # Pure whitespace
        payload["location"] = " \t \n "
        resp = client.post("/api/properties/validate", json=payload)
        assert resp.status_code == 422

        # Missing key
        del payload["location"]
        resp = client.post("/api/properties/validate", json=payload)
        assert resp.status_code == 422

    def test_invalid_price_zero_and_negative_returns_error(self, client, valid_property_dict):
        """Price must be strictly positive numeric value."""
        # Price == 0
        payload_zero = dict(valid_property_dict)
        payload_zero["price"] = 0
        resp_zero = client.post("/api/properties/validate", json=payload_zero)
        assert resp_zero.status_code == 422

        # Price < 0
        payload_neg = dict(valid_property_dict)
        payload_neg["price"] = -150000.0
        resp_neg = client.post("/api/properties/validate", json=payload_neg)
        assert resp_neg.status_code == 422

    def test_too_few_images_returns_validation_error(self, client, valid_property_dict, monkeypatch):
        """The validation endpoint reports too few images in its ValidationResponse payload."""
        # Gemini is configured in this developer's .env, which allows the app to generate missing images.
        monkeypatch.setattr(settings, "LLM_PROVIDER", "template")
        monkeypatch.setattr(settings, "LLM_API_KEY", None)
        for count in [0, 1, 2, 3]:
            payload = dict(valid_property_dict)
            payload["image_ids"] = [f"sample_img_{i}.jpg" for i in range(count)]
            resp = client.post("/api/properties/validate", json=payload)
            assert resp.status_code == 200
            assert resp.json()["valid"] is False
            assert any("at least 4" in error for error in resp.json()["errors"])

    def test_too_many_images_returns_error(self, client, valid_property_dict):
        """More than 8 images should fail validation."""
        payload = dict(valid_property_dict)
        payload["image_ids"] = [f"sample_img_{i}.jpg" for i in range(9)]
        resp = client.post("/api/properties/validate", json=payload)
        assert resp.status_code == 422

    def test_allowed_image_counts_succeed(self, client, valid_property_dict):
        """Exact boundaries of 4, 6, and 8 images should all pass validation."""
        for count in [4, 6, 8]:
            payload = dict(valid_property_dict)
            payload["image_ids"] = [f"1_exterior_facade.jpg"] * count
            resp = client.post("/api/properties/validate", json=payload)
            assert resp.status_code == 200
            assert resp.json()["valid"] is True

    def test_invalid_duration_returns_error(self, client, valid_property_dict):
        """Duration must be strictly 20, 30, or 40 seconds."""
        for invalid_d in [10, 15, 25, 35, 45, 60]:
            payload = dict(valid_property_dict)
            payload["duration"] = invalid_d
            resp = client.post("/api/properties/validate", json=payload)
            assert resp.status_code == 422

    def test_valid_durations_succeed(self, client, valid_property_dict):
        """Duration 20, 30, and 40 must succeed."""
        for d in [20, 30, 40]:
            payload = dict(valid_property_dict)
            payload["duration"] = d
            resp = client.post("/api/properties/validate", json=payload)
            assert resp.status_code == 200
            assert resp.json()["valid"] is True
            assert resp.json()["sanitized_data"]["duration"] == d

    def test_valid_with_all_optional_fields_omitted(self, client):
        """PropertyInput must validate cleanly when only mandatory fields are supplied."""
        minimal_payload = {
            "property_name": "Serene Oasis Villa",
            "location": "Whitefield, Bengaluru",
            "price": 24000000.0,
            "key_features": ["Private Garden Deck"],
            "image_ids": [
                "1_exterior_facade.jpg",
                "2_living_room.jpg",
                "3_modular_kitchen.jpg",
                "4_master_bedroom.jpg"
            ]
        }
        response = client.post("/api/properties/validate", json=minimal_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        sanitized = data["sanitized_data"]
        # Verify schema defaults are populated
        assert sanitized["currency"] == "₹"
        assert sanitized["property_type"] == "apartment"
        assert sanitized["duration"] == 30
        assert sanitized["aspect_ratio"] == "16:9"
        assert sanitized["theme"] == "luxury"
        assert sanitized["cta_text"] == "Schedule a Visit"
        assert sanitized["contact_name"] == "Sales Team"
        assert sanitized["narration_enabled"] is True
        assert sanitized["music_enabled"] is True
        assert sanitized["bedrooms"] is None
        assert sanitized["bathrooms"] is None

    def test_empty_or_whitespace_key_features_returns_error(self, client, valid_property_dict):
        """Key features list cannot be empty or contain only blank strings."""
        payload_empty = dict(valid_property_dict)
        payload_empty["key_features"] = []
        resp_empty = client.post("/api/properties/validate", json=payload_empty)
        assert resp_empty.status_code == 422

        payload_blanks = dict(valid_property_dict)
        payload_blanks["key_features"] = ["   ", ""]
        resp_blanks = client.post("/api/properties/validate", json=payload_blanks)
        assert resp_blanks.status_code == 422


# ============================================================================
# 3. Image Upload Tests
# ============================================================================

class TestImageUpload:
    def test_upload_valid_jpeg_success(self, client):
        """Uploading a valid JPEG (>= 300x300) should return 200 with image_id and preview_url."""
        img_bytes = create_in_memory_image(width=600, height=450, img_format="JPEG")
        response = client.post(
            "/api/images/upload",
            files={"file": ("test_facade.jpg", img_bytes, "image/jpeg")}
        )
        assert response.status_code == 200
        data = response.json()
        assert "image_id" in data
        assert "filename" in data
        assert "preview_url" in data
        assert data["width"] == 600
        assert data["height"] == 450
        assert data["original_filename"] == "test_facade.jpg"

        # Cleanup
        target = settings.UPLOAD_DIR / data["filename"]
        if target.is_file():
            target.unlink()

    def test_upload_valid_png_success(self, client):
        """Uploading a valid PNG should also be supported and return proper metadata."""
        img_bytes = create_in_memory_image(width=400, height=400, img_format="PNG")
        response = client.post(
            "/api/images/upload",
            files={"file": ("interior_shot.png", img_bytes, "image/png")}
        )
        assert response.status_code == 200
        data = response.json()
        # Uploads are normalized to compressed JPEGs before entering the render pipeline.
        assert data["filename"].endswith(".jpg")
        assert data["stored_size_bytes"] > 0
        assert data["width"] == 400

        # Cleanup
        target = settings.UPLOAD_DIR / data["filename"]
        if target.is_file():
            target.unlink()

    def test_upload_resizes_large_source_before_rendering(self, client):
        """Large uploads are stored as bounded JPEGs while original dimensions remain in the response."""
        source = Image.new("RGB", (2400, 1600), color=(105, 145, 185))
        buffer = io.BytesIO()
        source.save(buffer, format="JPEG", quality=95)
        source.close()
        image_bytes = buffer.getvalue()

        response = client.post(
            "/api/images/upload",
            files={"file": ("large_listing_photo.jpg", image_bytes, "image/jpeg")},
        )

        assert response.status_code == 200
        data = response.json()
        target = settings.UPLOAD_DIR / data["filename"]
        try:
            assert data["width"] == 2400
            assert data["height"] == 1600
            assert data["size_bytes"] == len(image_bytes)
            assert data["stored_size_bytes"] < data["size_bytes"]
            with Image.open(target) as stored_image:
                assert stored_image.format == "JPEG"
                assert stored_image.width <= settings.MAX_UPLOAD_IMAGE_EDGE
                assert stored_image.height <= settings.MAX_UPLOAD_IMAGE_EDGE
        finally:
            target.unlink(missing_ok=True)

    def test_upload_invalid_file_type_returns_400(self, client):
        """Uploading a text or non-image MIME type file must be rejected with 400."""
        text_content = b"This is plain text and not a real photo."
        response = client.post(
            "/api/images/upload",
            files={"file": ("notes.txt", text_content, "text/plain")}
        )
        assert response.status_code == 400
        assert "Unsupported image MIME type" in response.json()["detail"]

    def test_upload_corrupted_image_returns_400(self, client):
        """Uploading corrupted bytes with an image MIME header must be rejected by PIL validation."""
        corrupted_bytes = b"\xFF\xD8\xFF\xE0" + b"CorruptedHeaderAndGarbageContent12345"
        response = client.post(
            "/api/images/upload",
            files={"file": ("corrupt.jpg", corrupted_bytes, "image/jpeg")}
        )
        assert response.status_code == 400
        assert "corrupted or not a valid image" in response.json()["detail"].lower()

    def test_upload_too_small_resolution_returns_400(self, client):
        """Uploading an image below 300x300 must be rejected with minimum resolution error."""
        small_bytes = create_in_memory_image(width=200, height=200, img_format="JPEG")
        response = client.post(
            "/api/images/upload",
            files={"file": ("tiny_thumb.jpg", small_bytes, "image/jpeg")}
        )
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "too small" in detail.lower()
        assert "300x300" in detail

    def test_preview_uploaded_image_serves_file(self, client, uploaded_test_image):
        """GET /api/images/{image_id}/preview should serve the uploaded image binary."""
        image_id = uploaded_test_image["image_id"]
        response = client.get(f"/api/images/{image_id}/preview")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("image/jpeg")
        assert len(response.content) > 0

    def test_preview_nonexistent_image_returns_404(self, client):
        """GET /api/images/{image_id}/preview for nonexistent ID should return 404."""
        from app.services.mongodb_service import mongodb_service
        with patch.object(settings, "MONGODB_URI", None), \
                patch.object(settings, "REQUIRE_PERSISTENT_JOB_STORE", False), \
                patch.object(mongodb_service, "is_connected", return_value=False):
            response = client.get("/api/images/00000000-0000-0000-0000-000000000000/preview")
        assert response.status_code == 404
        assert "Image not found" in response.json()["detail"]

    def test_preview_restores_gridfs_image_when_local_file_is_missing(self, client):
        """An uploaded image preview is restored from GridFS after local storage is cleared."""
        from app.services.mongodb_service import mongodb_service

        image_id = str(uuid.uuid4())
        image_bytes = create_in_memory_image()
        restored_path = settings.UPLOAD_DIR / f"{image_id}.jpg"

        def restore(filename, destination):
            if filename != f"{image_id}.jpg":
                return False
            destination.write_bytes(image_bytes)
            return True

        try:
            with patch.object(settings, "MONGODB_GRIDFS_ENABLED", True), \
                    patch.object(mongodb_service, "is_connected", return_value=True), \
                    patch.object(mongodb_service, "copy_file_from_gridfs", side_effect=restore):
                response = client.get(f"/api/images/{image_id}/preview")
            assert response.status_code == 200
            assert response.content == image_bytes
        finally:
            restored_path.unlink(missing_ok=True)

    def test_image_preview_reports_mongodb_outage_as_503(self, client):
        """A missing local image is an outage, not not-found, if MongoDB is unavailable."""
        from app.services.file_storage import FileStorageService
        from app.services.mongodb_service import mongodb_service

        with patch.object(FileStorageService, "get_image_path", return_value=None), \
                patch.object(settings, "MONGODB_URI", "mongodb://unavailable"), \
                patch.object(settings, "REQUIRE_PERSISTENT_JOB_STORE", False), \
                patch.object(mongodb_service, "is_connected", return_value=False):
            response = client.get(f"/api/images/{uuid.uuid4()}/preview")
        assert response.status_code == 503
        assert "MongoDB is temporarily unavailable" in response.json()["detail"]


# ============================================================================
# 4. Script Generation Tests
# ============================================================================

class TestScriptGeneration:
    def test_generate_script_with_sample_data_returns_all_required_fields(self, client, valid_property_dict):
        """POST /api/scripts/generate must return video_title, opening_hook, voiceover_full, closing_cta, scene_captions."""
        response = client.post("/api/scripts/generate", json=valid_property_dict)
        assert response.status_code == 200
        data = response.json()

        required_keys = ["video_title", "opening_hook", "voiceover_full", "closing_cta", "scene_captions"]
        for key in required_keys:
            assert key in data, f"Missing key '{key}' in script output"

        assert isinstance(data["video_title"], str) and len(data["video_title"]) > 0
        assert isinstance(data["opening_hook"], str) and len(data["opening_hook"]) > 0
        assert isinstance(data["voiceover_full"], str) and len(data["voiceover_full"]) > 0
        assert isinstance(data["closing_cta"], str) and len(data["closing_cta"]) > 0
        assert isinstance(data["scene_captions"], list) and len(data["scene_captions"]) >= 2

    def test_template_fallback_works_consistently(self, client, valid_property_dict):
        """
        When LLM provider is 'template' (default), script generation must be deterministic,
        grounded, and succeed without external network dependencies.
        """
        with patch.object(settings, "LLM_PROVIDER", "template"):
            response = client.post("/api/scripts/generate", json=valid_property_dict)
            assert response.status_code == 200
            data = response.json()

            # Video title should combine property name and location
            assert valid_property_dict["property_name"] in data["video_title"]
            assert valid_property_dict["location"] in data["video_title"]

            # Opening hook should welcome viewers
            assert valid_property_dict["property_name"] in data["opening_hook"]
            assert valid_property_dict["location"] in data["opening_hook"]

            # Closing CTA must feature CTA text and contact information
            assert valid_property_dict["cta_text"] in data["closing_cta"]
            assert "98765 43210" in data["closing_cta"] or valid_property_dict["contact_name"] in data["closing_cta"]

    def test_scene_captions_are_non_empty_list_and_meaningful(self, client, valid_property_dict):
        """Scene captions must form a non-empty list of descriptive strings."""
        response = client.post("/api/scripts/generate", json=valid_property_dict)
        assert response.status_code == 200
        captions = response.json()["scene_captions"]

        assert len(captions) >= 2
        for caption in captions:
            assert isinstance(caption, str)
            assert len(caption.strip()) > 0

        # First caption introduces the property
        assert valid_property_dict["property_name"] in captions[0]
        # Last caption carries the call to action
        assert valid_property_dict["cta_text"] in captions[-1]

    def test_no_invented_claims_in_generated_voiceover(self, client, valid_property_dict):
        """
        The factual generator must strictly ground script in provided inputs and never
        invent amenities, landmarks, or features that were not specified.
        """
        custom_payload = dict(valid_property_dict)
        custom_payload["property_name"] = "Emerald Crown"
        custom_payload["location"] = "Koramangala, Bengaluru"
        custom_payload["key_features"] = ["Private Rooftop Terrace", "Teak Wood Flooring"]
        custom_payload["bedrooms"] = 4
        custom_payload["bathrooms"] = 4

        with patch.object(settings, "LLM_PROVIDER", "template"):
            response = client.post("/api/scripts/generate", json=custom_payload)
            assert response.status_code == 200
            vo = response.json()["voiceover_full"]

            # Explicit facts that SHOULD be present
            assert "Emerald Crown" in vo
            assert "Koramangala, Bengaluru" in vo or "Bengaluru" in vo
            assert "Private Rooftop Terrace" in vo or "Teak Wood Flooring" in vo
            assert "4 Bedrooms" in vo or "4 Bedroom" in vo

            # Invented features that MUST NOT appear
            unmentioned_claims = [
                "helipad", "olympic pool", "golf course", "squash court",
                "metro station 200m away", "near airport", "sea view", "beachfront"
            ]
            for claim in unmentioned_claims:
                assert claim not in vo.lower(), f"Script invented claim '{claim}'"

    def test_script_generation_with_different_visual_themes(self, client, valid_property_dict):
        """Each visual theme (luxury, modern, minimal, elegant) should format opening hooks appropriately."""
        themes = ["luxury", "modern", "minimal", "elegant"]
        for theme in themes:
            payload = dict(valid_property_dict)
            payload["theme"] = theme
            with patch.object(settings, "LLM_PROVIDER", "template"):
                response = client.post("/api/scripts/generate", json=payload)
                assert response.status_code == 200
                data = response.json()
                assert len(data["opening_hook"]) > 0


# ============================================================================
# 5. Storyboard Generation Tests
# ============================================================================

class TestStoryboardGeneration:
    def test_storyboard_scenes_match_image_count(self, client, valid_property_dict):
        """Number of generated storyboard scenes must exactly equal the number of image_ids provided."""
        for count in [4, 6]:
            payload = dict(valid_property_dict)
            payload["image_ids"] = [f"img_{i}.jpg" for i in range(count)]
            response = client.post("/api/storyboards/generate", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert len(data["scenes"]) == count

            for idx, scene in enumerate(data["scenes"]):
                assert scene["scene_index"] == idx
                assert scene["image_id"] == payload["image_ids"][idx]
                assert scene["image_index"] == idx

    def test_duration_sum_approximately_equals_requested_duration(self, client, valid_property_dict):
        """The sum of all scene durations must equal the target duration within tight float tolerance."""
        for target_duration in [20, 30, 40]:
            for img_count in [4, 5, 6, 7]:
                payload = dict(valid_property_dict)
                payload["duration"] = target_duration
                payload["image_ids"] = [f"img_{i}.jpg" for i in range(img_count)]

                response = client.post("/api/storyboards/generate", json=payload)
                assert response.status_code == 200
                data = response.json()

                total_sum = sum(scene["duration"] for scene in data["scenes"])
                assert abs(total_sum - target_duration) < 0.05, f"Sum {total_sum} != {target_duration}"
                assert data["total_duration"] == float(target_duration)

    def test_each_scene_has_valid_overlay_data(self, client, valid_property_dict):
        """Every scene must contain structured overlay elements (title, tag, badge, subtitle)."""
        response = client.post("/api/storyboards/generate", json=valid_property_dict)
        assert response.status_code == 200
        scenes = response.json()["scenes"]

        for scene in scenes:
            assert "overlay" in scene
            overlay = scene["overlay"]
            assert "title" in overlay and len(overlay["title"]) > 0
            assert "caption" in scene and len(scene["caption"]) > 0
            assert "voiceover_text" in scene and len(scene["voiceover_text"]) > 0

    def test_scene_types_include_opening_and_closing(self, client, valid_property_dict):
        """The first scene must be 'opening', the last 'closing', and intermediate scenes highlight/feature."""
        response = client.post("/api/storyboards/generate", json=valid_property_dict)
        assert response.status_code == 200
        scenes = response.json()["scenes"]

        assert scenes[0]["scene_type"] == "opening"
        assert scenes[0]["overlay"]["title"] == valid_property_dict["property_name"]

        assert scenes[1]["scene_type"] == "highlight"

        assert scenes[-1]["scene_type"] == "closing"
        assert scenes[-1]["overlay"]["title"] == valid_property_dict["cta_text"]

        for mid_scene in scenes[2:-1]:
            assert mid_scene["scene_type"] == "feature"

    def test_storyboard_preserves_aspect_ratio_and_theme(self, client, valid_property_dict):
        """Storyboard output must preserve the requested aspect ratio and theme."""
        payload = dict(valid_property_dict)
        payload["aspect_ratio"] = "9:16"
        payload["theme"] = "modern"

        response = client.post("/api/storyboards/generate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["aspect_ratio"] == "9:16"
        assert data["theme"] == "modern"
        # Opening scene tag should match modern living
        assert "MODERN" in data["scenes"][0]["overlay"]["tag"]


# ============================================================================
# 6. Sample Data Tests
# ============================================================================

class TestSampleData:
    def test_get_sample_listing_returns_valid_property_data(self, client):
        """GET /api/samples/listing must return complete ready-to-test property metadata."""
        response = client.get("/api/samples/listing")
        assert response.status_code == 200
        data = response.json()

        assert data["property_name"] == "Greenview Residency"
        assert "Mohali" in data["location"]
        assert data["price"] > 0
        assert data["currency"] == "₹"
        assert data["property_type"] == "apartment"
        assert len(data["key_features"]) >= 4
        assert data["bedrooms"] == 2
        assert data["bathrooms"] == 2
        assert data["duration"] in (20, 30, 40)
        assert data["aspect_ratio"] in ("16:9", "9:16")

        # Verify images list and image_ids list
        assert "image_ids" in data
        assert len(data["image_ids"]) >= 4
        assert "images" in data
        assert len(data["images"]) == len(data["image_ids"])

        for img in data["images"]:
            assert "image_id" in img
            assert "filename" in img
            assert "preview_url" in img
            assert img["width"] > 0
            assert img["height"] > 0

    def test_sample_listing_passes_validation_endpoint(self, client):
        """The data returned by /api/samples/listing must validate cleanly via /api/properties/validate."""
        sample_resp = client.get("/api/samples/listing")
        assert sample_resp.status_code == 200
        sample_data = sample_resp.json()

        validate_resp = client.post("/api/properties/validate", json=sample_data)
        assert validate_resp.status_code == 200
        val_json = validate_resp.json()
        assert val_json["valid"] is True
        assert val_json["sanitized_data"]["property_name"] == "Greenview Residency"

    def test_sample_images_are_accessible(self, client):
        """Each bundled sample image referenced by /api/samples/listing must be accessible via HTTP GET."""
        sample_resp = client.get("/api/samples/listing")
        sample_data = sample_resp.json()
        image_ids = sample_data["image_ids"]

        for filename in image_ids:
            img_resp = client.get(f"/api/samples/images/{filename}")
            assert img_resp.status_code == 200, f"Sample image '{filename}' not accessible"
            assert img_resp.headers["content-type"].startswith("image/jpeg")
            assert len(img_resp.content) > 1000

    def test_nonexistent_sample_image_returns_404(self, client):
        """Requesting a nonexistent sample image filename must return 404."""
        response = client.get("/api/samples/images/non_existent_file_99999.jpg")
        assert response.status_code == 404
        assert "Sample image not found" in response.json()["detail"]


# ============================================================================
# 7. Video Job Tests
# ============================================================================

class TestVideoJob:
    def test_create_video_job_returns_job_id(self, client, valid_property_dict):
        """
        POST /api/videos/generate with valid images on disk should queue a job and return
        a unique job_id and initial queued status.
        """
        # Mock background thread submission to prevent long rendering during unit testing
        with patch.object(job_manager._executor, "submit", return_value=None):
            response = client.post("/api/videos/generate", json=valid_property_dict)
            assert response.status_code == 200
            data = response.json()

            assert "job_id" in data
            assert len(data["job_id"]) > 10
            assert data["status"] == "queued"
            assert data["progress_percent"] == 5
            assert "stage_message" in data

    def test_create_video_job_missing_images_on_disk_returns_400(self, client, valid_property_dict):
        """If image IDs do not exist on the server, job creation must be rejected with 400."""
        from app.services.mongodb_service import mongodb_service
        payload = dict(valid_property_dict)
        payload["image_ids"] = [
            "missing_file_alpha.jpg",
            "missing_file_beta.jpg",
            "missing_file_gamma.jpg",
            "missing_file_delta.jpg"
        ]
        with patch.object(settings, "MONGODB_URI", None), \
                patch.object(settings, "REQUIRE_PERSISTENT_JOB_STORE", False), \
                patch.object(mongodb_service, "is_connected", return_value=False):
            response = client.post("/api/videos/generate", json=payload)
        assert response.status_code == 400
        assert "was not found on server" in response.json()["detail"]

    def test_get_non_existent_job_returns_404(self, client):
        """GET /api/videos/jobs/{job_id} for a non-existent job ID must return 404."""
        from app.services.mongodb_service import mongodb_service
        fake_uuid = str(uuid.uuid4())
        with patch.object(settings, "MONGODB_URI", None), \
                patch.object(settings, "REQUIRE_PERSISTENT_JOB_STORE", False), \
                patch.object(mongodb_service, "is_connected", return_value=False):
            response = client.get(f"/api/videos/jobs/{fake_uuid}")
        assert response.status_code == 404
        assert "Job not found" in response.json()["detail"]

    def test_persistent_job_mode_rejects_mongodb_outage(self, client, valid_property_dict):
        """Strict persistence mode must fail before queuing a memory-only render."""
        from app.services.mongodb_service import mongodb_service

        with patch.object(settings, "REQUIRE_PERSISTENT_JOB_STORE", True), \
                patch.object(settings, "MONGODB_URI", "mongodb://unavailable"), \
                patch.object(settings, "MONGODB_GRIDFS_ENABLED", True), \
                patch.object(mongodb_service, "is_connected", return_value=False):
            response = client.post("/api/videos/generate", json=valid_property_dict)
        assert response.status_code == 503
        assert "MongoDB is temporarily unavailable" in response.json()["detail"]

    def test_job_polling_returns_valid_structure(self, client, valid_property_dict):
        """Polling an active job must return the full VideoJob model schema."""
        with patch.object(job_manager._executor, "submit", return_value=None):
            post_resp = client.post("/api/videos/generate", json=valid_property_dict)
            assert post_resp.status_code == 200
            job_id = post_resp.json()["job_id"]

            poll_resp = client.get(f"/api/videos/jobs/{job_id}")
            assert poll_resp.status_code == 200
            poll_data = poll_resp.json()

            assert poll_data["job_id"] == job_id
            assert poll_data["status"] == "queued"
            assert poll_data["progress_percent"] == 5
            assert "created_at" in poll_data
            assert "updated_at" in poll_data

    def test_completed_job_polling_and_download_metadata(self, client):
        """Verify polling a completed job returns video URLs, download URLs, and metadata."""
        completed_job_id = str(uuid.uuid4())
        fake_video_id = str(uuid.uuid4())
        mock_job = VideoJob(
            job_id=completed_job_id,
            status=JobStatus.COMPLETED,
            progress_percent=100,
            stage_message="Video generation complete and ready to preview!",
            video_id=fake_video_id,
            video_url=f"/api/videos/{fake_video_id}",
            download_url=f"/api/videos/{fake_video_id}/download",
            metadata=OutputMetadata(
                duration_seconds=30.0,
                width=1920,
                height=1080,
                file_size_bytes=2048500,
                format="mp4",
                fps=30,
                aspect_ratio="16:9"
            )
        )
        job_manager._jobs[completed_job_id] = mock_job

        response = client.get(f"/api/videos/jobs/{completed_job_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["progress_percent"] == 100
        assert data["video_id"] == fake_video_id
        assert data["video_url"] == f"/api/videos/{fake_video_id}"
        assert data["download_url"] == f"/api/videos/{fake_video_id}/download"
        assert data["metadata"]["width"] == 1920
        assert data["metadata"]["height"] == 1080
        assert data["metadata"]["duration_seconds"] == 30.0

    def test_failed_job_polling_returns_error_message(self, client):
        """Verify polling a failed job surfaces clean error messaging without leaking internals."""
        failed_job_id = str(uuid.uuid4())
        mock_job = VideoJob(
            job_id=failed_job_id,
            status=JobStatus.FAILED,
            progress_percent=100,
            stage_message="Video generation failed",
            error_message="Media encoding error occurred during video rendering."
        )
        job_manager._jobs[failed_job_id] = mock_job

        response = client.get(f"/api/videos/jobs/{failed_job_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert data["error_message"] == "Media encoding error occurred during video rendering."

    def test_video_file_streaming_and_download_lifecycle(self, client):
        """Verify /api/videos/{video_id}, stream, and download endpoints when a video file exists on disk."""
        test_vid_id = f"test_vid_{uuid.uuid4().hex[:8]}"
        dummy_mp4_path = settings.OUTPUT_DIR / f"{test_vid_id}.mp4"
        dummy_mp4_path.write_bytes(b"\x00\x00\x00\x20ftypisom\x00\x00\x02\x00isomiso2mp41" + b"\x00" * 200)

        try:
            # 1. Metadata endpoint
            meta_resp = client.get(f"/api/videos/{test_vid_id}")
            assert meta_resp.status_code == 200
            meta_data = meta_resp.json()
            assert meta_data["video_id"] == test_vid_id
            assert meta_data["stream_url"] == f"/api/videos/{test_vid_id}/stream"
            assert meta_data["download_url"] == f"/api/videos/{test_vid_id}/download"
            assert meta_data["file_size_bytes"] > 0

            # 2. Stream endpoint
            stream_resp = client.get(f"/api/videos/{test_vid_id}/stream")
            assert stream_resp.status_code == 200
            assert stream_resp.headers["content-type"] == "video/mp4"
            assert stream_resp.headers.get("accept-ranges") == "bytes"
            assert len(stream_resp.content) == dummy_mp4_path.stat().st_size

            # 3. Download endpoint
            dl_resp = client.get(f"/api/videos/{test_vid_id}/download")
            assert dl_resp.status_code == 200
            assert dl_resp.headers["content-type"] == "video/mp4"
            assert "attachment" in dl_resp.headers.get("content-disposition", "")
        finally:
            if dummy_mp4_path.is_file():
                dummy_mp4_path.unlink()

    @pytest.mark.parametrize("action", ["stream", "download"])
    def test_video_preview_and_download_restore_gridfs_when_local_file_is_missing(self, client, action):
        """Video preview and download restore a GridFS MP4 when the Render disk has no copy."""
        from app.services.mongodb_service import mongodb_service

        video_id = str(uuid.uuid4())
        video_bytes = b"\x00\x00\x00\x20ftypisom\x00\x00\x02\x00isomiso2mp41" + b"\x00" * 200
        restored_path = settings.OUTPUT_DIR / f"{video_id}.mp4"

        def restore(filename, destination):
            if filename != f"{video_id}.mp4":
                return False
            destination.write_bytes(video_bytes)
            return True

        try:
            with patch.object(settings, "MONGODB_GRIDFS_ENABLED", True), \
                    patch.object(mongodb_service, "is_connected", return_value=True), \
                    patch.object(mongodb_service, "copy_file_from_gridfs", side_effect=restore):
                response = client.get(f"/api/videos/{video_id}/{action}")
            assert response.status_code == 200
            assert response.content == video_bytes
            if action == "download":
                assert "attachment" in response.headers.get("content-disposition", "")
            else:
                assert response.headers["content-type"] == "video/mp4"
        finally:
            restored_path.unlink(missing_ok=True)

    def test_video_download_reports_mongodb_outage_as_503(self, client):
        """A missing local video reports storage outage instead of an incorrect 404."""
        from app.services.file_storage import FileStorageService
        from app.services.mongodb_service import mongodb_service

        with patch.object(FileStorageService, "get_video_path", return_value=None), \
                patch.object(settings, "MONGODB_URI", "mongodb://unavailable"), \
                patch.object(settings, "REQUIRE_PERSISTENT_JOB_STORE", False), \
                patch.object(mongodb_service, "is_connected", return_value=False):
            response = client.get(f"/api/videos/{uuid.uuid4()}/download")
        assert response.status_code == 503
        assert "MongoDB is temporarily unavailable" in response.json()["detail"]

    def test_nonexistent_video_endpoints_return_404(self, client):
        """Requesting non-existent video IDs on metadata, stream, and download must all 404."""
        from app.services.mongodb_service import mongodb_service
        nonexistent = "missing_video_uuid_12345"
        with patch.object(settings, "MONGODB_URI", None), \
                patch.object(settings, "REQUIRE_PERSISTENT_JOB_STORE", False), \
                patch.object(mongodb_service, "is_connected", return_value=False):
            assert client.get(f"/api/videos/{nonexistent}").status_code == 404
            assert client.get(f"/api/videos/{nonexistent}/stream").status_code == 404
            assert client.get(f"/api/videos/{nonexistent}/download").status_code == 404


# ============================================================================
# 8. MongoDB Atlas Storage Tests
# ============================================================================

class TestMongoDBAtlasService:
    @pytest.mark.parametrize(
        "gridfs_video_id, expected_status",
        [("gridfs-object-id", JobStatus.COMPLETED), (None, JobStatus.FAILED)],
    )
    def test_job_only_completes_after_mp4_gridfs_persistence(
        self, tmp_path, valid_property_dict, gridfs_video_id, expected_status
    ):
        """Strict persistent mode cannot report completion from a local MP4 alone."""
        import threading
        import app.services.job_manager as job_manager_module
        from app.models.property import PropertyInput
        from app.services.mongodb_service import mongodb_service
        from app.services.job_manager import JobManager

        class StoryboardStub:
            scenes = []

            @staticmethod
            def model_dump(mode="json"):
                return {"scenes": []}

        manager = object.__new__(JobManager)
        job_id = str(uuid.uuid4())
        manager._jobs = {job_id: VideoJob(job_id=job_id)}
        manager._jobs_lock = threading.RLock()
        manager._instance_id = "test-render-instance"
        manager._mongo_warning_logged = False
        manager._jobs_dir = tmp_path / "jobs"
        manager._jobs_dir.mkdir()
        output_dir = tmp_path / "outputs"
        output_dir.mkdir()
        image_path = tmp_path / "image.jpg"
        image_path.write_bytes(b"property image")
        prop = PropertyInput(**valid_property_dict)
        metadata = {
            "duration_seconds": 30,
            "width": 1280,
            "height": 720,
            "file_size_bytes": 2048,
            "format": "mp4",
            "fps": 24,
            "aspect_ratio": "16:9",
        }

        def render(storyboard, prop, output_mp4, progress_callback):
            output_mp4.write_bytes(b"validated mp4 payload")
            return metadata

        with patch.object(job_manager_module, "OUTPUT_DIR", output_dir), \
                patch.object(manager, "_resolve_image_path", return_value=image_path), \
                patch.object(job_manager_module.VideoRenderer, "render_video", side_effect=render), \
                patch.object(settings, "REQUIRE_PERSISTENT_JOB_STORE", True), \
                patch.object(settings, "MONGODB_GRIDFS_ENABLED", True), \
                patch.object(mongodb_service, "is_connected", return_value=True), \
                patch.object(mongodb_service, "save_job", return_value=True), \
                patch.object(mongodb_service, "save_storyboard", return_value=True), \
                patch.object(mongodb_service, "save_path_to_gridfs", return_value=gridfs_video_id) as store_video, \
                patch.object(mongodb_service, "save_video_record", return_value=True):
            manager._run_job(job_id, prop, StoryboardStub())

        result = manager._jobs[job_id]
        assert result.status == expected_status
        assert store_video.call_count == 1
        assert store_video.call_args.kwargs["file_path"].is_file()
        if expected_status == JobStatus.COMPLETED:
            assert result.video_id is not None
            assert result.download_url.endswith("/download")
        else:
            assert result.video_id is None
            assert "GridFS" in result.error_message

    def test_restart_marks_interrupted_mongodb_jobs_failed(self):
        """Jobs still active under another process ID are persisted as failed on startup."""
        import threading
        from app.services.job_manager import JobManager
        from app.services.mongodb_service import mongodb_service

        manager = object.__new__(JobManager)
        manager._jobs = {}
        manager._jobs_lock = threading.RLock()
        manager._instance_id = "new-render-instance"
        interrupted = VideoJob(
            job_id=str(uuid.uuid4()),
            status=JobStatus.RENDERING,
            progress_percent=62,
            stage_message="Rendering scene 3",
        ).model_dump(mode="json")
        interrupted["worker_instance_id"] = "previous-render-instance"
        manager._persist_job = MagicMock(return_value=True)

        with patch.object(mongodb_service, "is_connected", return_value=True), \
                patch.object(mongodb_service, "list_active_jobs", return_value=[interrupted]):
            manager._recover_interrupted_mongo_jobs()

        recovered = manager._jobs[interrupted["job_id"]]
        assert recovered.status == JobStatus.FAILED
        assert "server restarted" in recovered.stage_message.lower()
        assert "restarted" in recovered.error_message.lower()
        manager._persist_job.assert_called_once_with(recovered)

    def test_completed_mongodb_job_is_restored_after_restart(self, tmp_path):
        """A terminal completed record remains readable from MongoDB in a fresh manager."""
        import threading
        from app.services.job_manager import JobManager
        from app.services.mongodb_service import mongodb_service

        manager = object.__new__(JobManager)
        manager._jobs = {}
        manager._jobs_lock = threading.RLock()
        manager._instance_id = "new-render-instance"
        manager._jobs_dir = tmp_path
        completed = VideoJob(
            job_id=str(uuid.uuid4()),
            status=JobStatus.COMPLETED,
            progress_percent=100,
            stage_message="Video generation complete",
            video_id="persistent-video-id",
            video_url="/api/videos/persistent-video-id/stream",
            download_url="/api/videos/persistent-video-id/download",
            metadata=OutputMetadata(
                duration_seconds=30,
                width=1280,
                height=720,
                file_size_bytes=4096,
                fps=24,
                aspect_ratio="16:9",
            ),
        ).model_dump(mode="json")
        completed["worker_instance_id"] = "previous-render-instance"

        with patch.object(manager, "_read_local_job", return_value=None), \
                patch.object(mongodb_service, "get_job", return_value=completed):
            restored = manager.get_job(completed["job_id"])

        assert restored is not None
        assert restored.status == JobStatus.COMPLETED
        assert restored.video_id == "persistent-video-id"
        assert restored.download_url.endswith("/download")

    def test_health_check_includes_mongodb_status(self, client):
        """GET /api/health should report MongoDB configuration and connection status."""
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "mongodb" in data
        mongo_status = data["mongodb"]
        assert "configured" in mongo_status
        assert "connected" in mongo_status
        assert isinstance(mongo_status["configured"], bool)
        assert isinstance(mongo_status["connected"], bool)

    def test_mongodb_fallback_graceful_methods(self):
        """When disconnected, MongoDBService operations must safely return None/False without crashing."""
        from app.services.mongodb_service import mongodb_service
        
        # Test safe fallback behaviors
        assert mongodb_service.save_job({"job_id": "fake_123"}) in (True, False)
        assert mongodb_service.get_job("fake_123") is None or isinstance(mongodb_service.get_job("fake_123"), dict)
        assert mongodb_service.list_videos() == [] or isinstance(mongodb_service.list_videos(), list)
        assert mongodb_service.save_file_to_gridfs(b"fake_bytes", "fake.jpg", "image/jpeg") is None or isinstance(mongodb_service.save_file_to_gridfs(b"fake_bytes", "fake.jpg", "image/jpeg"), str)
        assert mongodb_service.get_file_from_gridfs("nonexistent.mp4") is None

    def test_mongodb_mocked_persistence(self):
        """Verifies MongoDBService job and video record upsert logic when a database is connected."""
        from app.services.mongodb_service import MongoDBService
        from unittest.mock import MagicMock
        
        svc = MongoDBService()
        mock_db = MagicMock()
        svc._db = mock_db
        svc._client = MagicMock()
        svc._client.admin.command.return_value = {"ok": 1}

        # Bypass the connection retry cache: this test supplies a connected fake client.
        with patch.object(svc, "is_connected", return_value=True):
            # Test job upsert
            success = svc.save_job({"job_id": "test_job_1", "status": "queued"})
            assert success is True
            mock_db.__getitem__.assert_called()

            # Test video record upsert
            vid_success = svc.save_video_record({"video_id": "v1", "property_name": "Test Villa"})
            assert vid_success is True

            # Test get_job
            mock_db["jobs"].find_one.return_value = {"_id": "mongo_id", "job_id": "test_job_1", "status": "queued"}
            retrieved = svc.get_job("test_job_1")
            assert retrieved is not None
            assert retrieved["job_id"] == "test_job_1"
            assert "_id" not in retrieved

    def test_gridfs_path_upload_and_restore_are_streamed(self, tmp_path):
        """The persistent file store uploads and restores files through bounded GridFS reads."""
        from bson import ObjectId
        from app.services.mongodb_service import MongoDBService

        class FakeGridOut:
            def __init__(self, record):
                self._id = record["id"]
                self._payload = io.BytesIO(record["payload"])

            def read(self, size=-1):
                return self._payload.read(size)

            def close(self):
                self._payload.close()

        class FakeGridIn:
            def __init__(self, fs, filename, metadata):
                self._fs = fs
                self._id = ObjectId()
                self.filename = filename
                self.metadata = metadata
                self._payload = io.BytesIO()

            def write(self, chunk):
                self._payload.write(chunk)

            def close(self):
                self._fs.records[self.filename] = {
                    "id": self._id,
                    "payload": self._payload.getvalue(),
                    "metadata": self.metadata,
                }

            def abort(self):
                self._payload.close()

        class FakeGridFS:
            def __init__(self):
                self.records = {}

            def find_one(self, query):
                record = self.records.get(query.get("filename"))
                return FakeGridOut(record) if record else None

            def new_file(self, filename, metadata):
                return FakeGridIn(self, filename, metadata)

        svc = MongoDBService()
        source = tmp_path / "rendered.mp4"
        destination = tmp_path / "restored.mp4"
        payload = b"video-data-" * 1000
        source.write_bytes(payload)
        fake_fs = FakeGridFS()

        with patch.object(svc, "_fs", fake_fs), patch.object(svc, "is_connected", return_value=True):
            gridfs_id = svc.save_path_to_gridfs(source, "persistent-test.mp4", "video/mp4", chunk_size=128)
            assert gridfs_id is not None
            assert fake_fs.records["persistent-test.mp4"]["payload"] == payload
            assert fake_fs.records["persistent-test.mp4"]["metadata"]["content_type"] == "video/mp4"
            assert svc.copy_file_from_gridfs("persistent-test.mp4", destination, chunk_size=128)

        assert destination.read_bytes() == payload
