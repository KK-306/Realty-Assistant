from fastapi import APIRouter, HTTPException
from app.models.property import PropertyInput, ValidationResponse

router = APIRouter(prefix="/api/properties", tags=["Properties"])

@router.post("/validate", response_model=ValidationResponse)
def validate_property_details(prop: PropertyInput):
    """
    Validates all property inputs, formats, image count constraints, and duration options.
    """
    errors = []
    
    # Check image count constraints
    if len(prop.image_ids) < 4:
        errors.append("At least 4 property images must be uploaded (4 to 8 required).")
    elif len(prop.image_ids) > 8:
        errors.append("A maximum of 8 property images is allowed.")
        
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
