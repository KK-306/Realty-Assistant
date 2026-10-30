from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from app.config import SAMPLE_DIR
from app.services.file_storage import FileStorageService

router = APIRouter(prefix="/api/samples", tags=["Samples"])

@router.get("/listing")
def get_sample_listing():
    """
    Returns the ready-to-test demonstration property listing for 'Greenview Residency'
    complete with 6 verified local sample images.
    """
    images = FileStorageService.get_sample_images()
    return {
        "property_name": "Greenview Residency",
        "location": "Sector 82, Mohali, Punjab",
        "price": 8500000,
        "currency": "₹",
        "price_display": "₹85 Lakh",
        "property_type": "apartment",
        "key_features": [
            "Modular Italian Kitchen",
            "Spacious Balcony with Parkland View",
            "Reserved Covered Parking",
            "Abundant Natural Daylight"
        ],
        "bedrooms": 2,
        "bathrooms": 2,
        "description": "Exquisite 2-BHK luxury apartment featuring contemporary styling, modular fittings, panoramic parkland views, and dedicated covered parking in prime Mohali.",
        "contact_name": "Apex Prime Realty",
        "contact_details": "+91 98765 43210 | apex@realtydemo.com",
        "cta_text": "Schedule a Private Viewing",
        "duration": 30,
        "aspect_ratio": "16:9",
        "theme": "luxury",
        "voice_accent": "en-IN-PrabhatNeural",
        "narration_enabled": True,
        "music_enabled": True,
        "images": images,
        "image_ids": [img["image_id"] for img in images]
    }

@router.get("/video")
def get_sample_video():
    """
    Returns the stream URL of an existing pre-rendered demo video if available.
    """
    from app.config import OUTPUT_DIR
    outputs = sorted(list(OUTPUT_DIR.glob("*.mp4")), key=lambda p: p.stat().st_mtime, reverse=True)
    if outputs:
        video_id = outputs[0].stem
        return {
            "available": True,
            "video_id": video_id,
            "stream_url": f"/api/videos/{video_id}/stream",
            "download_url": f"/api/videos/{video_id}/download"
        }
    return {"available": False}

@router.get("/images/{filename}")
def serve_sample_image(filename: str):
    """
    Serves bundled sample images safely.
    """
    safe_name = Path(filename).name
    img_path = SAMPLE_DIR / safe_name
    if not img_path.is_file():
        raise HTTPException(status_code=404, detail="Sample image not found.")
    return FileResponse(img_path, media_type="image/jpeg")

