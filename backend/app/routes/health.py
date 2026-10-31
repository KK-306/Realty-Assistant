import shutil
import subprocess
from fastapi import APIRouter
from app.config import settings
from app.services.mongodb_service import mongodb_service

router = APIRouter(prefix="/api/health", tags=["Health"])

@router.get("")
def health_check():
    """
    Checks FFmpeg installation, storage accessibility, and configured AI services.
    """
    ffmpeg_exe = settings.get_ffmpeg_path()
    ffmpeg_available = False
    ffmpeg_version = "Unknown"

    try:
        res = subprocess.run([ffmpeg_exe, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
        if res.returncode == 0:
            ffmpeg_available = True
            first_line = res.stdout.split("\n")[0]
            ffmpeg_version = first_line[:60]
    except Exception as e:
        ffmpeg_version = f"Error: {e}"

    return {
        "status": "healthy" if ffmpeg_available else "degraded",
        "ffmpeg": {
            "available": ffmpeg_available,
            "path": ffmpeg_exe,
            "version": ffmpeg_version
        },
        "llm_provider": settings.LLM_PROVIDER,
        "llm_configured": bool(settings.LLM_API_KEY),
        "tts_provider": settings.TTS_PROVIDER,
        "storage": {
            "uploads_dir": str(settings.UPLOAD_DIR),
            "outputs_dir": str(settings.OUTPUT_DIR)
        },
        "mongodb": mongodb_service.get_status()
    }
