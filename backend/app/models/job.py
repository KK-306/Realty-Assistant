from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class JobStatus(str, Enum):
    QUEUED = "queued"
    VALIDATING = "validating"
    SCRIPTING = "scripting"
    PREPARING = "preparing"
    RENDERING = "rendering"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"

class OutputMetadata(BaseModel):
    duration_seconds: float
    width: int
    height: int
    file_size_bytes: int
    format: str = "mp4"
    fps: int = 30
    aspect_ratio: str

class VideoJob(BaseModel):
    job_id: str
    status: JobStatus = JobStatus.QUEUED
    progress_percent: int = Field(0, ge=0, le=100)
    stage_message: str = "Job submitted"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    video_id: Optional[str] = None
    video_url: Optional[str] = None
    download_url: Optional[str] = None
    metadata: Optional[OutputMetadata] = None
    error_message: Optional[str] = None
