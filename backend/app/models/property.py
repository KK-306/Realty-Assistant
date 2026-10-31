from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

class PropertyType(str, Enum):
    APARTMENT = "apartment"
    VILLA = "villa"
    INDEPENDENT_HOUSE = "independent_house"
    PLOT = "plot"
    COMMERCIAL = "commercial"
    OTHER = "other"

class VisualTheme(str, Enum):
    LUXURY = "luxury"
    MODERN = "modern"
    MINIMAL = "minimal"
    ELEGANT = "elegant"

class AspectRatio(str, Enum):
    LANDSCAPE = "16:9"
    VERTICAL = "9:16"

class PropertyInput(BaseModel):
    property_name: str = Field(..., min_length=2, max_length=100, description="Name or title of the property")
    location: str = Field(..., min_length=2, max_length=150, description="City, locality or state")
    price: float = Field(..., gt=0, description="Property price in numeric amount")
    currency: str = Field("₹", min_length=1, max_length=10, description="Currency symbol or code (e.g. ₹, $, AED)")
    price_display: Optional[str] = Field(None, max_length=50, description="Formatted price string, e.g. '₹85 Lakh'")
    property_type: PropertyType = Field(PropertyType.APARTMENT, description="Type of property")
    key_features: List[str] = Field(..., min_length=1, max_length=15, description="List of verified property features")
    bedrooms: Optional[int] = Field(None, ge=0, le=50, description="Number of bedrooms, if applicable")
    bathrooms: Optional[int] = Field(None, ge=0, le=50, description="Number of bathrooms, if applicable")
    description: Optional[str] = Field(None, max_length=1500, description="Optional property overview")
    contact_name: Optional[str] = Field("Sales Team", max_length=100, description="Agent or firm name")
    contact_details: Optional[str] = Field(None, max_length=120, description="Phone number or email")
    cta_text: str = Field("Schedule a Visit", min_length=2, max_length=60, description="Closing call to action")
    duration: int = Field(30, description="Desired video duration in seconds (20, 30, 40)")
    aspect_ratio: AspectRatio = Field(AspectRatio.LANDSCAPE, description="Video aspect ratio: 16:9 or 9:16")
    theme: VisualTheme = Field(VisualTheme.LUXURY, description="Visual branding theme")
    voice_accent: Optional[str] = Field("en-US-BrianNeural", description="AI voice accent and tone")
    narration_enabled: bool = Field(True, description="Enable voiceover narration")
    music_enabled: bool = Field(True, description="Enable ambient background music")
    script_text: Optional[str] = Field(None, max_length=5000, description="Optional draft narration for Gemini to refine")
    image_ids: List[str] = Field(default_factory=list, max_length=8, description="Ordered list of up to 8 uploaded image IDs; Gemini can generate missing scenes")

    @field_validator("property_name", "location")
    @classmethod
    def strip_and_check_non_empty(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Field cannot be empty or whitespace.")
        return s

    @field_validator("key_features")
    @classmethod
    def validate_features(cls, features: List[str]) -> List[str]:
        cleaned = [f.strip() for f in features if f and f.strip()]
        if not cleaned:
            raise ValueError("At least one valid key feature must be provided.")
        return cleaned

    @field_validator("duration")
    @classmethod
    def validate_duration(cls, v: int) -> int:
        if v not in (20, 30, 40):
            raise ValueError("Duration must be exactly 20, 30, or 40 seconds.")
        return v

class ValidationResponse(BaseModel):
    valid: bool
    message: str
    errors: List[str] = []
    sanitized_data: Optional[PropertyInput] = None
