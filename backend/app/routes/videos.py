from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from app.models.property import PropertyInput
from app.models.storyboard import StoryboardOutput
from app.models.job import VideoJob
from app.services.job_manager import job_manager
from app.services.file_storage import FileStorageService
from app.services.mongodb_service import mongodb_service

router = APIRouter(prefix="/api/videos", tags=["Videos"])


class VideoGenerationRequest(PropertyInput):
    storyboard_preview: StoryboardOutput | None = None

@router.post("/generate")
def create_video_render_job(request: VideoGenerationRequest):
    """
    Submits a video generation task to the background queue and returns the tracking job_id.
    """
    # Validation checks
    prop = PropertyInput(**request.model_dump(exclude={"storyboard_preview"}))
    storyboard_preview = request.storyboard_preview

    if len(prop.image_ids) < 4 or len(prop.image_ids) > 8:
        raise HTTPException(status_code=400, detail="Between 4 and 8 property images are required.")

    if storyboard_preview and [scene.image_id for scene in storyboard_preview.scenes] != prop.image_ids:
        raise HTTPException(status_code=400, detail="Storyboard images do not match the submitted property images.")

    for img_id in prop.image_ids:
        path = FileStorageService.get_image_path(img_id)
        if not path or not path.is_file():
            raise HTTPException(status_code=400, detail=f"Image {img_id} was not found on server.")

    job = job_manager.create_job(prop, storyboard_preview=storyboard_preview)
    return {
        "job_id": job.job_id,
        "status": job.status.value,
        "progress_percent": job.progress_percent,
        "stage_message": job.stage_message
    }

@router.get("/jobs/{job_id}", response_model=VideoJob)
def get_job_status(job_id: str):
    """
    Polls the real-time status, progress, stage message, and download links for a video job.
    """
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job

@router.get("")
@router.get("/")
def list_rendered_videos():
    """
    Returns a list of all rendered promotional videos stored on MongoDB Atlas / server.
    """
    from app.config import OUTPUT_DIR
    import datetime
    
    # Check MongoDB collection first
    mongo_videos = []
    if mongodb_service.is_connected():
        mongo_videos = mongodb_service.list_videos()

    if mongo_videos:
        return {"videos": mongo_videos, "count": len(mongo_videos)}

    # Fallback to scanning local output directory
    videos = []
    if OUTPUT_DIR.is_dir():
        files = sorted(OUTPUT_DIR.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
        for f in files:
            stat = f.stat()
            mtime = datetime.datetime.fromtimestamp(stat.st_mtime, tz=datetime.timezone.utc).isoformat()
            videos.append({
                "video_id": f.stem,
                "property_name": "Promotional Property Showcase",
                "location": "Sector 82, Mohali, Punjab",
                "file_size_bytes": stat.st_size,
                "duration": 30,
                "aspect_ratio": "16:9",
                "stream_url": f"/api/videos/{f.stem}/stream",
                "download_url": f"/api/videos/{f.stem}/download",
                "created_at": mtime,
                "date": mtime
            })
    return {"videos": videos, "count": len(videos)}

@router.get("/{video_id}")
def get_video_metadata(video_id: str):
    """
    Returns metadata for a rendered video.
    """
    # Check MongoDB for enriched record
    if mongodb_service.is_connected():
        doc = mongodb_service.get_video_record(video_id)
        if doc:
            return doc

    video_path = FileStorageService.get_video_path(video_id)
    if not video_path or not video_path.is_file():
        raise HTTPException(status_code=404, detail="Video file not found.")

    return {
        "video_id": video_id,
        "file_size_bytes": video_path.stat().st_size,
        "stream_url": f"/api/videos/{video_id}/stream",
        "download_url": f"/api/videos/{video_id}/download"
    }

@router.get("/{video_id}/stream")
def stream_video(video_id: str):
    """
    Serves the MP4 video stream for inline HTML5 video playback.
    """
    video_path = FileStorageService.get_video_path(video_id)
    if not video_path or not video_path.is_file():
        raise HTTPException(status_code=404, detail="Video not found.")

    return FileResponse(
        video_path,
        media_type="video/mp4",
        headers={"Accept-Ranges": "bytes"}
    )

@router.get("/{video_id}/download")
def download_video(video_id: str):
    """
    Forces MP4 file download with clean attachment filename.
    """
    video_path = FileStorageService.get_video_path(video_id)
    if not video_path or not video_path.is_file():
        raise HTTPException(status_code=404, detail="Video not found.")

    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename=f"property_promotional_video_{video_id[:8]}.mp4"
    )
