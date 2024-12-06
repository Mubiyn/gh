from fastapi import APIRouter, HTTPException
from services.rhino_operations import export_geometry
from models.models import ExportParams

router = APIRouter()

@router.post("/export/")
def export(params: ExportParams):
    try:
        return export_geometry(params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting geometry: {e}")
