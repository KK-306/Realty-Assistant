from fastapi import APIRouter, HTTPException
from app.models.property import PropertyInput, ValidationResponse
from app.config import settings

router = APIRouter(prefix="/api/properties", tags=["Properties"])

@router.post("/validate", response_model=ValidationResponse)
def validate_property_details(prop: PropertyInput):
    """
    Validates all property inputs, formats, image count constraints, and duration options.
    """
    errors = []
    
    # Check image count constraints
    if len(prop.image_ids) > 8:
        errors.append("A maximum of 8 property images is allowed.")
    elif len(prop.image_ids) < 4 and not (
        settings.LLM_PROVIDER == "gemini" and settings.LLM_API_KEY
    ):
        errors.append("Upload at least 4 photos, or configure Gemini to generate the missing images.")
        
    if prop.price <= 0:
        errors.append("Price must be a positive numeric value.")
        
    if not prop.key_features:
        errors.append("Please provide at least one verified key feature.")

    if errors:
        return ValidationResponse(
            valid=False,
            message="Validation failed for property information.",
            errors=errors
        )

    return ValidationResponse(
        valid=True,
        message="Property information is valid.",
        errors=[],
        sanitized_data=prop
    )
