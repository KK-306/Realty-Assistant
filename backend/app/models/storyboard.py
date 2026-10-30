from typing import List, Optional
from pydantic import BaseModel, Field

class SceneOverlay(BaseModel):
    tag: Optional[str] = Field(None, description="Small badge tag, e.g. 'FEATURED HIGHLIGHT' or 'PRIME RESIDENCE'")
    title: str = Field(..., description="Primary headline text")
    subtitle: Optional[str] = Field(None, description="Secondary descriptive line")
    badge: Optional[str] = Field(None, description="Price badge or highlight tag")
    footer: Optional[str] = Field(None, description="Contact information or location footer")

class StoryboardScene(BaseModel):
    scene_index: int = Field(..., ge=0)
    scene_type: str = Field(..., description="'opening', 'feature', 'highlight', or 'closing'")
    duration: float = Field(..., gt=0, description="Duration of this scene in seconds")
    image_id: str = Field(..., description="ID of the uploaded image for this scene")
    image_index: int = Field(..., description="0-based index in the user's selected image order")
    caption: str = Field(..., description="Human-readable on-screen caption")
    voiceover_text: str = Field(..., description="Voiceover spoken narration text for this scene")
    overlay: SceneOverlay

class ScriptOutput(BaseModel):
    video_title: str
    opening_hook: str
    voiceover_full: str
    closing_cta: str

class StoryboardOutput(BaseModel):
    script: ScriptOutput
    scenes: List[StoryboardScene]
    total_duration: float
    aspect_ratio: str
    theme: str
