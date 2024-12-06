from fastapi import APIRouter, HTTPException
from services.rhino_operations import run_grasshopper_definition
from models.models import GrasshopperParams

router = APIRouter()

@router.post("/run/")
def run_grasshopper(params: GrasshopperParams):
    try:
        result = run_grasshopper_definition(params.file_path, params.inputs)
        return {"result": result}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

