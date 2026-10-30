from fastapi import APIRouter, HTTPException
from app.models.property import PropertyInput
from app.models.storyboard import StoryboardOutput
from app.services.storyboard_service import StoryboardService

router = APIRouter(prefix="/api/storyboards", tags=["Storyboards"])

@router.post("/generate", response_model=StoryboardOutput)
def generate_storyboard(prop: PropertyInput):
    """
    Produces complete structured storyboard pacing each scene and mapping overlays.
    """
    try:
        storyboard = StoryboardService.generate_storyboard(prop)
        return storyboard
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to generate storyboard.")
