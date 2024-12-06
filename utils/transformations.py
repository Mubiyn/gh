import rhino3dm
import math

def apply_scale(brep, scale_factor):
    transform = rhino3dm.Transform.Scale(rhino3dm.Point3d(0, 0, 0), scale_factor)
    brep.Transform(transform)
    return brep

def apply_rotation(brep, angle_degrees, axis, center):
    radians = math.radians(angle_degrees)
    transform = rhino3dm.Transform.Rotation(radians, axis, center)
    brep.Transform(transform)
    return brep
