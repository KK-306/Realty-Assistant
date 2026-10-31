import json
import logging
import os
import threading
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from app.config import OUTPUT_DIR, settings
from app.models.job import JobStatus, OutputMetadata, VideoJob
from app.models.property import PropertyInput
from app.models.storyboard import StoryboardOutput
from app.services.mongodb_service import mongodb_service
from app.services.storyboard_service import StoryboardService
from app.services.video_renderer import VideoRenderer

logger = logging.getLogger(__name__)


class PersistentJobStoreUnavailable(RuntimeError):
    """Raised when deployment configuration requires MongoDB but it is unavailable."""


class JobManager:
    _instance = None
    _instance_lock = threading.Lock()
    _initialization_lock = threading.Lock()
    _terminal_statuses = {JobStatus.COMPLETED, JobStatus.FAILED}

    def __new__(cls):
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super(JobManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        with self._initialization_lock:
            if getattr(self, "_initialized", False):
                return

            self._jobs: Dict[str, VideoJob] = {}
            self._jobs_lock = threading.RLock()
            self._instance_id = str(uuid.uuid4())
            self._jobs_dir = settings.STORAGE_DIR / "jobs"
            self._jobs_dir.mkdir(parents=True, exist_ok=True)
            # On a 512 MB / fractional CPU instance, concurrent renders risk OOM.
            self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="video-render")
            self._mongo_warning_logged = False
            self._load_local_jobs()
            self._recover_interrupted_mongo_jobs()
            self._initialized = True

            if not settings.MONGODB_URI:
                logger.warning(
                    "MongoDB job persistence is not configured. Job checkpoints use local storage at %s; "
                    "that filesystem may be cleared on Render deploys or instance replacement.",
                    self._jobs_dir,
                )

    def _job_file(self, job_id: str) -> Path:
        return self._jobs_dir / f"{Path(job_id).name}.json"

    def _local_document(self, job: VideoJob) -> dict:
        document = job.model_dump(mode="json")
        document["worker_instance_id"] = self._instance_id
        return document

    def _save_local_job(self, job: VideoJob) -> bool:
        destination = self._job_file(job.job_id)
        temporary = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.tmp")
        try:
            with temporary.open("w", encoding="utf-8") as state_file:
                json.dump(self._local_document(job), state_file, ensure_ascii=False)
                state_file.flush()
                os.fsync(state_file.fileno())
            os.replace(temporary, destination)
            return True
        except OSError:
            logger.exception("Could not persist local state for video job %s", job.job_id)
            temporary.unlink(missing_ok=True)
            return False

    def _persist_job(self, job: VideoJob) -> bool:
        """Checkpoint every status locally and, when configured, in MongoDB."""
        local_ok = self._save_local_job(job)
        mongo_ok = mongodb_service.save_job(self._local_document(job))
        if settings.MONGODB_URI and not mongo_ok and not self._mongo_warning_logged:
            logger.warning(
                "MongoDB job checkpoint failed; local checkpoints are being used. "
                "They are not durable across Render deploys or instance replacement."
            )
            self._mongo_warning_logged = True
        if not local_ok and not mongo_ok:
            logger.error("Job %s has no available persistent checkpoint store", job.job_id)
        return mongo_ok

    def _load_local_jobs(self) -> None:
        for state_file in self._jobs_dir.glob("*.json"):
            try:
                with state_file.open("r", encoding="utf-8") as saved:
                    document = json.load(saved)
                worker_id = document.pop("worker_instance_id", None)
                job = VideoJob(**document)
                was_interrupted = job.status not in self._terminal_statuses
                if was_interrupted:
                    self._mark_restart_failure(job)
                self._jobs[job.job_id] = job
                if was_interrupted:
                    self._persist_job(job)
                else:
                    self._save_local_job(job)
                logger.info("Restored persisted video job %s with status %s", job.job_id, job.status.value)
                if worker_id != self._instance_id:
                    logger.info("Job %s belongs to a previous backend process", job.job_id)
            except Exception:
                logger.exception("Could not restore persisted job state from %s", state_file)

    def _recover_interrupted_mongo_jobs(self) -> None:
        """Mark jobs left active by a previous process as failed during startup."""
        if not mongodb_service.is_connected():
            return

        for document in mongodb_service.list_active_jobs():
            try:
                worker_id = document.get("worker_instance_id")
                job = VideoJob(**document)
                if job.status in self._terminal_statuses or worker_id == self._instance_id:
                    continue

                with self._jobs_lock:
                    existing = self._jobs.get(job.job_id)
                    if existing and existing.status in self._terminal_statuses:
                        job = existing
                    else:
                        self._mark_restart_failure(job)
                        self._jobs[job.job_id] = job

                if job.status == JobStatus.FAILED:
                    self._persist_job(job)
                    logger.warning("Marked interrupted MongoDB job %s as failed during startup", job.job_id)
            except Exception:
                logger.exception("Could not recover interrupted MongoDB job %s", document.get("job_id", "unknown"))

    @staticmethod
    def _mark_restart_failure(job: VideoJob) -> None:
        job.status = JobStatus.FAILED
        job.progress_percent = 100
        job.stage_message = "Video generation stopped after the server restarted"
        job.error_message = "The server restarted before this render finished. Please submit the video again."
        job.updated_at = datetime.now(timezone.utc)

    def create_job(self, prop: PropertyInput, storyboard_preview: Optional[StoryboardOutput] = None) -> VideoJob:
        if settings.REQUIRE_PERSISTENT_JOB_STORE:
            if not settings.MONGODB_URI or not settings.MONGODB_GRIDFS_ENABLED:
                raise PersistentJobStoreUnavailable(
                    "Persistent jobs require MONGODB_URI and MONGODB_GRIDFS_ENABLED=true."
                )
            if not mongodb_service.is_connected():
                raise PersistentJobStoreUnavailable("MongoDB is required for video jobs but is currently unavailable.")

        now = datetime.now(timezone.utc)
        job = VideoJob(
            job_id=str(uuid.uuid4()),
            status=JobStatus.QUEUED,
            progress_percent=5,
            stage_message="Job queued for processing",
            created_at=now,
            updated_at=now,
        )
        with self._jobs_lock:
            self._jobs[job.job_id] = job

        logger.info("Created video job %s (render queue workers=1)", job.job_id)
        mongo_saved = self._persist_job(job)
        if settings.REQUIRE_PERSISTENT_JOB_STORE and not mongo_saved:
            self._update_job(
                job.job_id,
                JobStatus.FAILED,
                100,
                "Persistent job storage unavailable",
                "MongoDB did not accept the initial job checkpoint. No render was started.",
            )
            raise PersistentJobStoreUnavailable("MongoDB could not persist the new video job.")

        try:
            if not mongodb_service.save_property(job.job_id, prop.model_dump(mode="json")):
                logger.warning("Property data for job %s was not persisted in MongoDB", job.job_id)
            future = self._executor.submit(self._run_job, job.job_id, prop, storyboard_preview)
            if isinstance(future, Future):
                future.add_done_callback(
                    lambda completed, current_id=job.job_id: self._handle_future_exit(current_id, completed)
                )
        except Exception as exc:
            logger.exception("Could not submit video job %s", job.job_id)
            self._update_job(
                job.job_id,
                JobStatus.FAILED,
                100,
                "Video job could not be queued",
                f"The render worker could not be started: {exc}",
            )
        return job

    def _handle_future_exit(self, job_id: str, future: Future) -> None:
        try:
            exc = future.exception()
        except Exception as callback_error:
            exc = callback_error
        if exc is None:
            return
        logger.error(
            "Video worker terminated unexpectedly for job %s",
            job_id,
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        self._update_job(
            job_id,
            JobStatus.FAILED,
            100,
            "Video generation worker stopped unexpectedly",
            f"The render worker stopped unexpectedly: {exc}",
        )

    def _read_local_job(self, job_id: str) -> Optional[dict]:
        state_file = self._job_file(job_id)
        if not state_file.is_file():
            return None
        try:
            with state_file.open("r", encoding="utf-8") as saved:
                return json.load(saved)
        except (OSError, ValueError):
            logger.exception("Could not read local state for video job %s", job_id)
            return None

    def get_job(self, job_id: str) -> Optional[VideoJob]:
        with self._jobs_lock:
            job = self._jobs.get(job_id)
        document = None
        if job is None:
            document = self._read_local_job(job_id)
            if document is None:
                document = mongodb_service.get_job(job_id)
            if document:
                worker_id = document.get("worker_instance_id")
                try:
                    job = VideoJob(**document)
                except Exception:
                    logger.exception("Could not restore job %s from persistent storage", job_id)
                    return None
                with self._jobs_lock:
                    self._jobs[job_id] = job
                if job.status not in self._terminal_statuses and worker_id != self._instance_id:
                    logger.warning("Job %s was active in another backend process; marking it failed", job_id)
                    self._mark_restart_failure(job)
                    self._persist_job(job)

        if job is not None and job.status not in self._terminal_statuses:
            # Older saved records have no worker id; without a live local worker, do not report them as running forever.
            local_document = self._read_local_job(job_id)
            worker_id = local_document.get("worker_instance_id") if local_document else self._instance_id
            if worker_id != self._instance_id:
                self._mark_restart_failure(job)
                self._persist_job(job)
        return job

    def _update_job(
        self,
        job_id: str,
        status: JobStatus,
        progress: int,
        stage: str,
        error: Optional[str] = None,
    ) -> None:
        with self._jobs_lock:
            job = self._jobs.get(job_id)
            if not job:
                logger.error("Cannot update missing video job %s to %s", job_id, status.value)
                return
            if job.status in self._terminal_statuses:
                logger.warning("Ignoring status update for terminal video job %s", job_id)
                return
            job.status = status
            job.progress_percent = progress
            job.stage_message = stage
            job.updated_at = datetime.now(timezone.utc)
            if error:
                job.error_message = error[:2000]
            snapshot = job.model_copy(deep=True)
        mongo_saved = self._persist_job(snapshot)
        if settings.REQUIRE_PERSISTENT_JOB_STORE and not mongo_saved and status != JobStatus.FAILED:
            with self._jobs_lock:
                current = self._jobs.get(job_id)
                if current and current.status not in self._terminal_statuses:
                    current.status = JobStatus.FAILED
                    current.progress_percent = 100
                    current.stage_message = "Persistent job storage became unavailable"
                    current.error_message = "MongoDB stopped accepting job checkpoints. The render was stopped; retry when storage is available."
                    current.updated_at = datetime.now(timezone.utc)
                    failed_snapshot = current.model_copy(deep=True)
                else:
                    failed_snapshot = None
            if failed_snapshot:
                self._save_local_job(failed_snapshot)
            raise PersistentJobStoreUnavailable("MongoDB stopped accepting job checkpoints; rendering was stopped.")
        logger.info("Video job %s status=%s progress=%s stage=%s", job_id, status.value, progress, stage)

    def _run_job(self, job_id: str, prop: PropertyInput, storyboard_preview: Optional[StoryboardOutput] = None) -> None:
        logger.info("Starting execution for video job %s", job_id)
        try:
            self._update_job(job_id, JobStatus.VALIDATING, 10, "Validating property details and images")
            for image_id in prop.image_ids:
                image_path = self._resolve_image_path(image_id)
                if image_path is None or not image_path.is_file():
                    raise FileNotFoundError(f"Property image {image_id} is missing on the render server.")

            self._update_job(job_id, JobStatus.SCRIPTING, 20, "Generating factual real estate script and scenes")
            logger.info("Storyboard generation started for video job %s", job_id)
            storyboard = storyboard_preview or StoryboardService.generate_storyboard(prop)
            logger.info("Storyboard generation completed for video job %s: %s scenes", job_id, len(storyboard.scenes))
            if not mongodb_service.save_storyboard(job_id, storyboard.model_dump(mode="json")):
                logger.warning("Storyboard for job %s was not persisted in MongoDB", job_id)

            self._update_job(job_id, JobStatus.PREPARING, 30, "Composing visual cards and preparing assets")
            video_id = str(uuid.uuid4())
            output_mp4_path = OUTPUT_DIR / f"{video_id}.mp4"

            def on_render_progress(pct: int, msg: str) -> None:
                self._update_job(job_id, JobStatus.RENDERING, pct, msg)

            logger.info("Video renderer started for job %s", job_id)
            metadata_dict = VideoRenderer.render_video(
                storyboard=storyboard,
                prop=prop,
                output_mp4=output_mp4_path,
                progress_callback=on_render_progress,
            )
            logger.info("Video renderer completed for job %s: %s", job_id, output_mp4_path)

            self._update_job(job_id, JobStatus.FINALIZING, 95, "Finalizing output and generating stream links")
            gridfs_video_id = None
            if mongodb_service.is_connected() and settings.MONGODB_GRIDFS_ENABLED:
                gridfs_video_id = mongodb_service.save_path_to_gridfs(
                    file_path=output_mp4_path,
                    filename=f"{video_id}.mp4",
                    content_type="video/mp4",
                    metadata={
                        "video_id": video_id,
                        "job_id": job_id,
                        "duration": metadata_dict["duration_seconds"],
                        "property_name": prop.property_name,
                    },
                )
            if settings.REQUIRE_PERSISTENT_JOB_STORE and not gridfs_video_id:
                raise RuntimeError("Rendered MP4 could not be persisted to GridFS; the job cannot be completed safely.")

            with self._jobs_lock:
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
                    aspect_ratio=metadata_dict["aspect_ratio"],
                )
            self._update_job(
                job_id,
                JobStatus.FINALIZING,
                97,
                "Rendered MP4 stored; finalizing video metadata",
            )

            video_saved = mongodb_service.save_video_record({
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
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            if not video_saved:
                logger.warning("Video metadata for job %s was not persisted in MongoDB", job_id)
                if settings.REQUIRE_PERSISTENT_JOB_STORE:
                    raise RuntimeError("Video metadata could not be persisted in MongoDB; the job cannot be completed safely.")

            self._update_job(job_id, JobStatus.COMPLETED, 100, "Video generation complete and ready to preview!")
            logger.info("Video job %s completed successfully. Video ID: %s", job_id, video_id)
        except Exception as exc:
            logger.exception("Video job %s encountered an error", job_id)
            clean_error = str(exc).strip() or type(exc).__name__
            self._update_job(job_id, JobStatus.FAILED, 100, "Video generation failed", clean_error)

    @staticmethod
    def _resolve_image_path(image_id: str) -> Optional[Path]:
        from app.services.file_storage import FileStorageService

        return FileStorageService.get_image_path(image_id)


job_manager = JobManager()
