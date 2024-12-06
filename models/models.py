from pydantic import BaseModel
from typing import List, Dict, Optional

class SphereParams(BaseModel):
    radius: float
    center_x: float = 0.0
    center_y: float = 0.0
    center_z: float = 0.0

class TransformParams(BaseModel):
    brep_str: str
    scale: float = 1.0
    rotation_degrees: float = 0.0

class ExportParams(BaseModel):
    brep_str: str
    format: str = "obj"

class GrasshopperParams(BaseModel):
    file_path: str
    inputs: dict

class BrepToMeshParams(BaseModel):
    brep_str: str  
    density: float = 0.5 



class MeshParams(BaseModel):
    name: str = ''
    type: str = "flexure_box"  # Type of mesh: "box", "sphere", "cylinder", or "flexure_box"
    length: float = 1.0  # Length of the box (if applicable)
    width: float = 1.0   # Width of the box (if applicable)
    height: float = 1.0  # Height of the box (if applicable)
    radius: float = 1.0  # Radius for sphere or cylinder (if applicable)
    
    # New fields for lattice flexures
    flexure_density: Optional[str] = None  # Lattice density: "low", "medium", "high"
    flexure_regions: Optional[List[Dict[str, float]]] = None  # List of regions for flexures
    
    # Example for `flexure_regions`: [{"start": 1.0, "end": 2.0}, {"start": 8.0, "end": 9.0}]
    # For sphere or cylinder


