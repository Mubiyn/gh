from pathlib import Path
import compute_rhino3d.Brep
import compute_rhino3d.Mesh
import rhino3dm
import math
import requests
from fastapi import HTTPException

from models.models import MeshParams
from utils.strings import BASE_URL


def create_mesh(params: MeshParams):
    print(f"Param is: {params}")
    try:
        if params.type == "box":
            # Create a simple box geometry
            box = rhino3dm.BoundingBox(
                rhino3dm.Point3d(0, 0, 0),
                rhino3dm.Point3d(params.length, params.width, params.height)
            )
            brep = box.ToBrep()
        
        elif params.type == "flexure_box":
            # Create the base box geometry
            box = rhino3dm.BoundingBox(
                rhino3dm.Point3d(0, 0, 0),
                rhino3dm.Point3d(params.length, params.width, params.height)
            )
            brep = box.ToBrep()

            # Apply lattice flexures
            flexure_regions = params.flexure_regions
            flexure_density = params.flexure_density

            if flexure_regions and flexure_density:
                brep = apply_lattice_flexures(brep, flexure_regions, flexure_density)
        
        elif params.type == "sphere":
            # Create a sphere geometry
            sphere = rhino3dm.Sphere(rhino3dm.Point3d(params.length, params.width, params.height), params.radius)
            brep = sphere.ToBrep()
        
        elif params.type == "cylinder":
            # Create a cylinder geometry
            cylinder = rhino3dm.Cylinder(
                rhino3dm.Circle(rhino3dm.Point3d(params.length, params.width, params.height), params.radius),
                params.height
            )
            brep = cylinder.ToBrep(True, True)
        
        else:
            raise ValueError("Unsupported mesh type")

        # Convert the brep to a mesh
        d = compute_rhino3d.Mesh.CreateFromBrep(brep)
        if not d or len(d) == 0:
            raise Exception("Failed to create a mesh from the Brep")

        # Assuming we use the first mesh
        mesh = d[0]

        # Save the mesh as an OBJ file
        obj_output_path = Path(f"{params.name}_mesh.obj")
        save_mesh_to_obj(mesh, obj_output_path)

        # Save the mesh and Brep to a Rhino file
        rhino_output_path = Path(f"{params.name}_geometry.3dm")
        save_to_rhino_file(brep, mesh, rhino_output_path)

        return {
            "message": f"{params.name.capitalize()} mesh created successfully",
            "obj_file_path": obj_output_path,
            "rhino_file_path": rhino_output_path,
        }
    
    except Exception as e:
        raise Exception(f"Error creating mesh: {e}")

def save_to_rhino_file(brep, mesh, file_path):
    try:
        rhino_file = rhino3dm.File3dm()

        # Add Brep to the file
        if brep and brep.IsValid:
            rhino_file.Objects.AddBrep(brep)

        # Add Mesh to the file
        if mesh and mesh.IsValid:
            rhino_file.Objects.AddMesh(mesh)

        # Save the file
        rhino_file.Write(str(file_path))
        return {"message": "Saved to Rhino file successfully", "file_path": str(file_path)}

    except Exception as e:
        raise Exception(f"Error saving to Rhino file: {e}")


def save_mesh_to_obj(mesh, file_path):
    try:
        with open(file_path, 'w') as obj_file:
            # Write vertices
            for vertex in mesh.Vertices:
                obj_file.write(f"v {vertex.X} {vertex.Y} {vertex.Z}\n")
            
            # Write normals
            for normal in mesh.Normals:
                obj_file.write(f"vn {normal.X} {normal.Y} {normal.Z}\n")
            
            # Write faces
            for face in mesh.Faces:
                if len(face) == 4:  # Quad face
                    obj_file.write(f"f {face[0]+1} {face[1]+1} {face[2]+1} {face[3]+1}\n")
                elif len(face) == 3:  # Triangle face
                    obj_file.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")
                else:
                    raise ValueError("Unsupported face type: faces must be triangles or quads")
        return {"message": "Mesh saved successfully", "file_path": str(file_path)}
    except Exception as e:
        raise ValueError(f"Error saving mesh to OBJ: {e}")




def apply_lattice_flexures(brep, regions, density):
    print("Generating lattice flexures::::")

    # Define lattice element size based on density
    density_map = {
        "low": 1.0,  # Larger elements, lower density
        "medium": 0.5,
        "high": 0.25  # Smaller elements, higher density
    }
    element_size = density_map.get(density, 0.5)  # Default to medium if undefined

    lattice_brep = brep  # Start with the input Brep

    for region in regions:
        x_min = region.get("x_min")
        x_max = region.get("x_max")
        y_min = region.get("y_min", brep.GetBoundingBox().Min.Y)
        y_max = region.get("y_max", brep.GetBoundingBox().Max.Y)
        z_min = region.get("z_min", brep.GetBoundingBox().Min.Z)
        z_max = region.get("z_max", brep.GetBoundingBox().Max.Z)

        if x_min is None or x_max is None:
            print(f"Skipping invalid region: {region}")
            continue

        # Create region box
        region_box = rhino3dm.BoundingBox(
            rhino3dm.Point3d(x_min, y_min, z_min),
            rhino3dm.Point3d(x_max, y_max, z_max)
        )
        box_brep = region_box.ToBrep()

        # Use Rhino.Compute to split the brep
        split_result = compute_rhino3d.Brep.Split(lattice_brep, box_brep, 0.01)  # 0.01 is the tolerance
        if not split_result or len(split_result) == 0:
            print(f"Splitting failed for region box: {region_box}")
            continue

        region_brep = split_result[0]  # Assume the first part is the desired one

        # Generate lattice and merge
        lattice = generate_lattice(region_brep, element_size)
        if not lattice or not lattice.IsValid:
            print(f"Skipping invalid lattice for region: {region}")
            continue

        print(f"Joining Breps: lattice_brep validity: {lattice_brep.IsValid}, lattice validity: {lattice.IsValid}")

        try:
            result = compute_rhino3d.Brep.JoinBreps([lattice_brep, lattice], 0.01)
            if not result or len(result) == 0:
                raise Exception("JoinBreps failed to return a valid Brep.")
            
            new_lattice_brep = result[0]  # Extract the first Brep
            if new_lattice_brep and isinstance(new_lattice_brep, rhino3dm.Brep):
                lattice_brep = new_lattice_brep  # Update lattice_brep
            else:
                raise Exception("JoinBreps returned an invalid result.")

        except Exception as e:
            print(f"Error during JoinBreps: {e}")
            continue

    print("Generated lattice flexures::::")
    return lattice_brep



def generate_lattice(region_brep, element_size):
    import rhino3dm
    import compute_rhino3d

    # Validate the input Brep
    if not isinstance(region_brep, rhino3dm.Brep) or not region_brep.IsValid:
        raise Exception("Invalid Brep provided to generate_lattice")

    # Get the bounding box of the Brep
    try:
        bbox = region_brep.GetBoundingBox()  # Ensure no arguments are passed
        min_pt = bbox.Min
        max_pt = bbox.Max
    except Exception as e:
        raise Exception(f"Error obtaining bounding box: {e}")

    # Initialize an empty lattice Brep
    lattice_brep = None

    # Iterate to create lattice struts

    x = min_pt.X

    while x < max_pt.X:

        y = min_pt.Y
        while y < max_pt.Y:

            z = min_pt.Z
            while z < max_pt.Z:
      
                # Define strut endpoints
                p1 = rhino3dm.Point3d(x, y, z)
                p2 = rhino3dm.Point3d(x + element_size, y + element_size, z + element_size)
      
                # Create a strut
                strut = create_strut(p1, p2)
                if strut is None or not strut.IsValid:
                    print(f"Skipping invalid strut: {p1} to {p2}")
                    z += element_size
                    continue

                # Join the strut to the lattice
       
                if lattice_brep is None:
                    lattice_brep = strut  # Initialize lattice_brep with the first valid strut
                else:
                    try:
                        result = compute_rhino3d.Brep.JoinBreps([lattice_brep, strut], 0.01)
                        if result and len(result) > 0:
                            lattice_brep = result[0]
                        else:
                            print(f"Failed to join strut at {p1}")
                    except Exception as e:
                        print(f"Error joining strut: {e}")

                z += element_size
            y += element_size
        x += element_size

    if lattice_brep is None:
        raise Exception("Failed to generate lattice structure")

    return lattice_brep




def create_strut(start, end):

    # Create a cylinder or strut between two points
    line = rhino3dm.Line(start, end)
    circle = rhino3dm.Circle(line.PointAt(0.5), 0.1)  # Strut radius = 0.1
    cylinder = rhino3dm.Cylinder(circle, line.Length)

    return cylinder.ToBrep(True, True)


def create_sphere(params):
    center = rhino3dm.Point3d(params.center_x, params.center_y, params.center_z)
    sphere = rhino3dm.Sphere(center, params.radius)
    brep = sphere.ToBrep()
    return {
        "radius": sphere.Radius,
        "center": {"x": center.X, "y": center.Y, "z": center.Z},
        "brep": brep.Encode()
    }

def transform_geometry(params):
    brep = rhino3dm.CommonObject.Decode(params.brep_str)
    if not isinstance(brep, rhino3dm.Brep):
        raise ValueError("Invalid Brep string provided")
    
    if params.scale != 1.0:
        scale_transform = rhino3dm.Transform.Scale(rhino3dm.Point3d(0, 0, 0), params.scale)
        brep.Transform(scale_transform)

    if params.rotation_degrees != 0.0:
        rotation_radians = math.radians(params.rotation_degrees)
        rotation_transform = rhino3dm.Transform.Rotation(
            rotation_radians, rhino3dm.Vector3d(0, 0, 1), rhino3dm.Point3d(0, 0, 0)
        )
        brep.Transform(rotation_transform)

    return {"message": "Transformation successful", "brep": brep.Encode()}


def convert_to_mesh(params):
    try:
        # Deserialize Brep from input string
        brep = rhino3dm.CommonObject.Decode(params.brep_str)
        if not isinstance(brep, rhino3dm.Brep):
            raise HTTPException(status_code=400, detail="Invalid Brep string provided")

        # Create mesh from Brep using Rhino.Compute
        meshes = compute_rhino3d.Mesh.CreateFromBrep(brep)
        if not meshes or len(meshes) == 0:
            raise Exception("Failed to create mesh from Brep")

        # Use the first mesh
        mesh = meshes[0]

        # Serialize mesh for return
        mesh_str = mesh.Encode()

        return {
            "message": "Mesh conversion successful",
            "mesh": mesh_str
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error converting to mesh: {e}")



def export_geometry(params):
    brep = rhino3dm.CommonObject.Decode(params.brep_str)
    file_name = f"geometry.{params.format}"
    try:
        if params.format == "obj":
            save_mesh_to_obj(brep, file_name)
        elif params.format == "3dm":
            save_to_rhino_file(brep, None, file_name)
        else:
            raise ValueError("Unsupported format")
        return {"message": "Export successful", "file_path": file_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting geometry: {e}")




def run_grasshopper_definition(file_path: str, inputs: dict):
    """
    Runs a Grasshopper definition via Rhino.Compute and returns the result.
    """
    try:
        payload = {
            "script": file_path,
            "values": [
                {
                    "ParamName": key,
                    "InnerTree": {
                        "(0)": [{"type": "System.String", "data": str(value)}]
                    }
                } for key, value in inputs.items()
            ]
        }

        url = f"{BASE_URL}grasshopper"
        response = requests.post(url, json=payload)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"Error from Rhino.Compute: {response.text}")

        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running Grasshopper definition: {e}")


