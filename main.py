from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import compute_rhino3d.Util as rc
import rhino3dm
import os
from dotenv import load_dotenv
import requests
from routes.geometry import router as geometry_router
from routes.export import router as export_router
from routes.grasshopper import router as grasshopper_router
from models.models import SphereParams
from utils.strings import API_KEY, BASE_URL

# Initialize FastAPI application once
app = FastAPI()

# Load environment variables
load_dotenv()

# Include routers before starting FastAPI
app.include_router(geometry_router, prefix="/geometry", tags=["Geometry"])
app.include_router(export_router, prefix="/export", tags=["Export"])
app.include_router(grasshopper_router, prefix="/grasshopper", tags=["Grasshopper"])

# Initialize Rhino.Compute
if not API_KEY:
    raise ValueError("API Key not found! Set RHINO_COMPUTE_API_KEY in your environment.")
rc.apiKey = API_KEY
rc.url = f"{BASE_URL}"

# Base Route
@app.get("/")
def read_root():
    return {"message": "Welcome to the Mubiyn's Compute API"}

# Healthcheck endpoint
@app.get("/healthcheck")
def rhino_compute_healthcheck():
    try:
        # Send an HTTP GET request to the Rhino.Compute server's healthcheck endpoint
        response = requests.get(f"{BASE_URL}healthcheck")
        
        # Check the status code
        if response.status_code == 200:
            return {"message": "Mubiyn's Rhino.Compute Wrapper is running", "status": response.content}
        else:
            raise HTTPException(status_code=response.status_code, detail="Rhino.Compute is not healthy")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to Rhino.Compute: {e}")
