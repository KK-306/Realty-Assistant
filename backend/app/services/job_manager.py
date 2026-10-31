import uuid
import threading
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Dict, Optional
from pathlib import Path

from app.config import OUTPUT_DIR, settings
from app.models.property import PropertyInput
from app.models.storyboard import StoryboardOutput
from app.models.job import VideoJob, JobStatus, OutputMetadata
from app.services.storyboard_service import StoryboardService
from app.services.video_renderer import VideoRenderer
from app.services.mongodb_service import mongodb_service

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

    def create_job(self, prop: PropertyInput, storyboard_preview: Optional[StoryboardOutput] = None) -> VideoJob:
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
        
        # Persist to MongoDB if connected
        try:
            mongodb_service.save_job(job.model_dump())
            mongodb_service.save_property(job_id, prop.model_dump())
        except Exception as e:
            logger.warning(f"Failed to record initial job {job_id} in MongoDB: {e}")

        # Submit to background thread pool
        self._executor.submit(self._run_job, job_id, prop, storyboard_preview)
        return job

    def get_job(self, job_id: str) -> Optional[VideoJob]:
        job = self._jobs.get(job_id)
        if job:
            return job
        
        # If not in memory, attempt to retrieve from MongoDB Atlas
        doc = mongodb_service.get_job(job_id)
        if doc:
            try:
                recovered = VideoJob(**doc)
                self._jobs[job_id] = recovered
                return recovered
            except Exception as e:
                logger.warning(f"Error restoring job {job_id} from MongoDB: {e}")
        return None

    def _update_job(self, job_id: str, status: JobStatus, progress: int, stage: str, error: Optional[str] = None):
        job = self._jobs.get(job_id)
        if job:
            job.status = status
            job.progress_percent = progress
            job.stage_message = stage
            job.updated_at = datetime.now(timezone.utc)
            if error:
                job.error_message = error
            # Update MongoDB
            try:
                mongodb_service.save_job(job.model_dump())
            except Exception:
                pass

    def _run_job(self, job_id: str, prop: PropertyInput, storyboard_preview: Optional[StoryboardOutput] = None):
        logger.info(f"Starting execution for video job {job_id}")
        try:
            # Stage 1: Validation
            self._update_job(job_id, JobStatus.VALIDATING, 10, "Validating property details and images")
            
            # Stage 2: Scripting & Storyboard
            self._update_job(job_id, JobStatus.SCRIPTING, 20, "Generating factual real estate script and scenes")
            storyboard = storyboard_preview or StoryboardService.generate_storyboard(prop)
            try:
                mongodb_service.save_storyboard(job_id, storyboard.model_dump())
            except Exception:
                pass

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

            # Persist MP4 to MongoDB GridFS if enabled
            gridfs_video_id = None
            if mongodb_service.is_connected() and settings.MONGODB_GRIDFS_ENABLED:
                try:
                    with open(output_mp4_path, "rb") as vf:
                        video_bytes = vf.read()
                    gridfs_video_id = mongodb_service.save_file_to_gridfs(
                        file_bytes=video_bytes,
                        filename=f"{video_id}.mp4",
                        content_type="video/mp4",
                        metadata={
                            "video_id": video_id,
                            "job_id": job_id,
                            "duration": metadata_dict["duration_seconds"],
                            "property_name": prop.property_name
                        }
                    )
                except Exception as gfs_err:
                    logger.warning(f"Could not upload video {video_id} to GridFS: {gfs_err}")

            job = self._jobs[job_id]
            job.video_id = video_id
            job.video_url = f"/api/videos/{video_id}/stream"
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

            # Persist completed video entry into MongoDB video library
            try:
                mongodb_service.save_video_record({
                    "video_id": video_id,
                    "job_id": job_id,
                    "property_name": prop.property_name,
                    "location": prop.location,
                    "price_display": prop.price_display or f"{prop.currency}{prop.price:,.0f}",
                    "file_size_bytes": metadata_dict["file_size_bytes"],
                    "duration": metadata_dict["duration_seconds"],
                    "aspect_ratio": metadata_dict["aspect_ratio"],
                    "stream_url": f"/api/videos/{video_id}/stream",
                    "download_url": f"/api/videos/{video_id}/download",
                    "gridfs_video_id": gridfs_video_id,
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
            except Exception as vid_err:
                logger.warning(f"Failed to save video record for {video_id} to MongoDB: {vid_err}")

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
