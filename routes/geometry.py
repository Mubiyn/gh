from fastapi import APIRouter, HTTPException
from models.models import MeshParams, SphereParams, TransformParams, BrepToMeshParams
from services.rhino_operations import create_mesh, create_sphere, transform_geometry, convert_to_mesh

router = APIRouter()


@router.post("/generate-mesh/")
def generate_mesh(params: MeshParams):
    
    try:
        return create_mesh(params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating mesh: {e}")

@router.post("/generate-sphere/")
def generate_sphere(params: SphereParams):
    try:
        return create_sphere(params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating sphere: {e}")

@router.post("/transform-geometry/")
def transform_geometry_endpoint(params: TransformParams):
    try:
        return transform_geometry(params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error transforming geometry: {e}")
    
@router.post("/convert-to-mesh/")
def convert_to_mesh_endpoint(params: BrepToMeshParams):
    try:
        return convert_to_mesh(params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error coverting to mesh: {e}")
