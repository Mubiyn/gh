from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import compute_rhino3d.Util as rc
import rhino3dm
import os
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()
API_KEY = os.getenv("RHINO_COMPUTE_API_KEY")

# Initialize Rhino.Compute
if not API_KEY:
    raise ValueError("API Key not found! Set RHINO_COMPUTE_API_KEY in your environment.")
rc.apiKey=(API_KEY)
rc.url = "http://localhost:6500/"


# Initialize FastAPI application
app = FastAPI()

# Define Pydantic models for input validation
class SphereInput(BaseModel):
    radius: float
    x: float = 0
    y: float = 0
    z: float = 0

class GrasshopperInput(BaseModel):
    file_path: str
    inputs: list[dict]

# Base Route
@app.get("/")
def read_root():
    return {"message": "Welcome to the Mubiyn's Compute API"}

    
# Healthcheck endpoint
@app.get("/healthcheck")
def rhino_compute_healthcheck():
    try:
        # Send an HTTP GET request to the Rhino.Compute server's healthcheck endpoint
        response = requests.get("http://localhost:6500/healthcheck")
        print(response)
        
        # Check the status code
        if response.status_code == 200:
            return {"message": "Mubiyn's Rhino.Compute Wrapper is running", "status": response.content}
        else:
            raise HTTPException(status_code=response.status_code, detail="Rhino.Compute is not healthy")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to Rhino.Compute: {e}")


@app.post("/create-sphere/")
def create_sphere(data: SphereInput):
    try:
        # Create a Rhino3dm Sphere
        center = rhino3dm.Point3d(data.x, data.y, data.z)
        sphere = rhino3dm.Sphere(center, data.radius)
        brep = sphere.ToBrep()  # Convert to Brep (Boundary Representation)

        # Return Sphere Data
        return {
            "radius": sphere.Radius,
            "center": {"x": sphere.Center.X, "y": sphere.Center.Y, "z": sphere.Center.Z},
            "brep": str(brep)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
