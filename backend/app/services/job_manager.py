import uuid
import threading
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Dict, Optional
from pathlib import Path

from app.config import OUTPUT_DIR
from app.models.property import PropertyInput
from app.models.storyboard import StoryboardOutput
from app.models.job import VideoJob, JobStatus, OutputMetadata
from app.services.storyboard_service import StoryboardService
from app.services.video_renderer import VideoRenderer

logger = logging.getLogger(__name__)

class JobManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(JobManager, cls).__new__(cls)
                cls._instance._jobs: Dict[str, VideoJob] = {}
                cls._instance._executor = ThreadPoolExecutor(max_workers=3)
        return cls._instance

    def create_job(self, prop: PropertyInput) -> VideoJob:
        job_id = str(uuid.uuid4())
        job = VideoJob(
            job_id=job_id,
            status=JobStatus.QUEUED,
            progress_percent=5,
            stage_message="Job queued for processing",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        self._jobs[job_id] = job
        # Submit to background thread pool
        self._executor.submit(self._run_job, job_id, prop)
        return job

    def get_job(self, job_id: str) -> Optional[VideoJob]:
        return self._jobs.get(job_id)

    def _update_job(self, job_id: str, status: JobStatus, progress: int, stage: str, error: Optional[str] = None):
        job = self._jobs.get(job_id)
        if job:
            job.status = status
            job.progress_percent = progress
            job.stage_message = stage
            job.updated_at = datetime.now(timezone.utc)
            if error:
                job.error_message = error

    def _run_job(self, job_id: str, prop: PropertyInput):
        logger.info(f"Starting execution for video job {job_id}")
        try:
            # Stage 1: Validation
            self._update_job(job_id, JobStatus.VALIDATING, 10, "Validating property details and images")
            
            # Stage 2: Scripting & Storyboard
            self._update_job(job_id, JobStatus.SCRIPTING, 20, "Generating factual real estate script and scenes")
            storyboard = StoryboardService.generate_storyboard(prop)

            # Stage 3: Preparing scenes
            self._update_job(job_id, JobStatus.PREPARING, 30, "Composing visual cards and preparing assets")

            video_id = str(uuid.uuid4())
            output_mp4_path = OUTPUT_DIR / f"{video_id}.mp4"

            # Progress callback for renderer
            def on_render_progress(pct: int, msg: str):
                self._update_job(job_id, JobStatus.RENDERING, pct, msg)

            # Stage 4: Render Video
            metadata_dict = VideoRenderer.render_video(
                storyboard=storyboard,
                prop=prop,
                output_mp4=output_mp4_path,
                progress_callback=on_render_progress
            )

            # Stage 5: Finalizing
            self._update_job(job_id, JobStatus.FINALIZING, 95, "Finalizing output and generating stream links")

            job = self._jobs[job_id]
            job.video_id = video_id
            job.video_url = f"/api/videos/{video_id}"
            job.download_url = f"/api/videos/{video_id}/download"
            job.metadata = OutputMetadata(
                duration_seconds=metadata_dict["duration_seconds"],
                width=metadata_dict["width"],
                height=metadata_dict["height"],
                file_size_bytes=metadata_dict["file_size_bytes"],
                format="mp4",
                fps=metadata_dict["fps"],
                aspect_ratio=metadata_dict["aspect_ratio"]
            )
            self._update_job(job_id, JobStatus.COMPLETED, 100, "Video generation complete and ready to preview!")
            logger.info(f"Video job {job_id} successfully completed. Video ID: {video_id}")

        except Exception as e:
            logger.exception(f"Video job {job_id} encountered an error: {e}")
            # Format clean error message without leaking sensitive internal paths
            clean_err = str(e)
            if "FFmpeg" in clean_err:
                clean_err = "Media encoding error occurred during video rendering."
            self._update_job(job_id, JobStatus.FAILED, 100, "Video generation failed", error=clean_err)

job_manager = JobManager()
