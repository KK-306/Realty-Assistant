from fastapi import APIRouter, HTTPException
from app.models.property import PropertyInput
from app.services.script_generator import ScriptGenerator

router = APIRouter(prefix="/api/scripts", tags=["Scripts"])

@router.post("/generate")
def generate_script(prop: PropertyInput):
    """
    Generates a factual promotional real estate script based strictly on user inputs.
    """
    try:
        script = ScriptGenerator.generate(prop)
        return script
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to generate script.")
