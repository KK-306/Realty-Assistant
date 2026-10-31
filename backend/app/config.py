import os
import shutil
from pathlib import Path
from typing import List, Optional

# Base directories
BACKEND_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = BACKEND_DIR.parent
APP_DIR = BACKEND_DIR / "app"
STORAGE_DIR = BACKEND_DIR / "storage"
UPLOAD_DIR = STORAGE_DIR / "uploads"
OUTPUT_DIR = STORAGE_DIR / "outputs"
ASSETS_DIR = APP_DIR / "assets"
SAMPLE_DIR = ASSETS_DIR / "sample_properties"
AUDIO_DIR = ASSETS_DIR / "audio"

# Load project-local secrets before settings are read. Environment variables set by
# the host still take precedence over values in the .env file.
try:
    from dotenv import load_dotenv
    load_dotenv(WORKSPACE_DIR / ".env", override=False)
except ImportError:
    # Deployments can provide configuration through the process environment.
    pass

# Ensure directories exist
for p in [UPLOAD_DIR, OUTPUT_DIR, SAMPLE_DIR, AUDIO_DIR]:
    p.mkdir(parents=True, exist_ok=True)

class Settings:
    # Directories
    UPLOAD_DIR = UPLOAD_DIR
    OUTPUT_DIR = OUTPUT_DIR
    SAMPLE_DIR = SAMPLE_DIR
    AUDIO_DIR = AUDIO_DIR
    STORAGE_DIR = STORAGE_DIR

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    CORS_ORIGINS: List[str] = [
        origin.strip().rstrip("/")
        for origin in os.getenv(
            "CORS_ORIGINS",
            ",".join([
                "https://realty-assistant-1.onrender.com",
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://localhost:3000",
                "http://127.0.0.1:3000",
            ]),
        ).split(",")
        if origin.strip()
    ]
    
    # Upload limits
    MAX_IMAGE_COUNT: int = 8
    MIN_IMAGE_COUNT: int = 4
    MAX_FILE_SIZE_MB: int = 15
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/webp"]
    
    # Video settings
    DEFAULT_DURATION: int = 30
    ALLOWED_DURATIONS: List[int] = [20, 30, 40]
    ALLOWED_ASPECT_RATIOS: List[str] = ["16:9", "9:16"]
    ALLOWED_THEMES: List[str] = ["luxury", "modern", "minimal", "elegant"]
    
    # Resolutions
    RESOLUTIONS = {
        "16:9": {"width": 1920, "height": 1080},
        "9:16": {"width": 1080, "height": 1920}
    }
    
    # LLM Configuration
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "template").lower()  # "gemini", "openai", "groq", "template"
    LLM_API_KEY: Optional[str] = os.getenv("LLM_API_KEY")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-3.8-flash")
    GEMINI_IMAGE_MODEL: str = os.getenv("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image")
    
    # TTS Configuration
    TTS_PROVIDER: str = os.getenv("TTS_PROVIDER", "edge_tts").lower()  # "edge_tts", "none"
    TTS_VOICE_EN: str = os.getenv("TTS_VOICE_EN", "en-US-BrianNeural")
    TTS_VOICE_IN: str = os.getenv("TTS_VOICE_IN", "en-IN-PrabhatNeural")
    
    # MongoDB Atlas Configuration
    MONGODB_URI: Optional[str] = os.getenv("MONGODB_URI")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "ra_property_studio")
    MONGODB_GRIDFS_ENABLED: bool = os.getenv("MONGODB_GRIDFS_ENABLED", "true").lower() in ("true", "1", "yes")

    # FFmpeg executable resolution
    @classmethod
    def get_ffmpeg_path(cls) -> str:
        # 1. Custom ENV override
        env_ffmpeg = os.getenv("FFMPEG_PATH")
        if env_ffmpeg and os.path.isfile(env_ffmpeg):
            return env_ffmpeg
            
        # 2. System PATH
        which_ffmpeg = shutil.which("ffmpeg")
        if which_ffmpeg:
            return which_ffmpeg
            
        # 3. imageio-ffmpeg package if installed
        try:
            import imageio_ffmpeg
            exe = imageio_ffmpeg.get_ffmpeg_exe()
            if exe and os.path.isfile(exe):
                return exe
        except Exception:
            pass
            
        # 4. Common Windows paths
        common_paths = [
            r"C:\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
            r"C:\Users\Kartik Karnwal\anaconda3\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
        ]
        for cp in common_paths:
            if os.path.isfile(cp):
                return cp
                
        return "ffmpeg"

settings = Settings()
