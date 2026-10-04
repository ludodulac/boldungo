"""Generic normalized image constraints and perspective projection for Scene/photo comparison."""
from __future__ import annotations
from enum import Enum
from math import cos, sin, radians
from pydantic import BaseModel, Field

class ImagePrimitiveKind(str, Enum):
    POINT="point"; LINE="line"; POLYLINE="polyline"; POLYGON="polygon"; BBOX="bbox"
    CONTACT="contact"; ALIGNMENT="alignment"; OCCLUSION="occlusion"; CONTINUATION="continuation"; SAME_OBJECT="same_object"

class NormalizedPoint(BaseModel):
    x: float=Field(ge=0,le=1); y: float=Field(ge=0,le=1)

class ImageConstraint(BaseModel):
    id:str
    kind:ImagePrimitiveKind
    points:list[NormalizedPoint]=Field(default_factory=list)
    scene_object_id:str|None=None
    relation_target_id:str|None=None
    statement:str
    confidence:float=Field(ge=0,le=1)

class PerspectiveCamera(BaseModel):
    yaw_degrees:float
    pitch_degrees:float
    roll_degrees:float=0
    focal_normalized:float=1.0
    center_x:float=.5
    center_y:float=.5
    scale:float=.08

def project_point(point:tuple[float,float,float], camera:PerspectiveCamera)->tuple[float,float]:
    # Generic weak-perspective camera: sufficient for first same-image-space diagnostic.
    x,y,z=point
    ya=radians(camera.yaw_degrees); pa=radians(camera.pitch_degrees); ra=radians(camera.roll_degrees)
    xr=cos(ya)*x-sin(ya)*y; yr=sin(ya)*x+cos(ya)*y
    zr=cos(pa)*z-sin(pa)*yr; depth=sin(pa)*z+cos(pa)*yr
    denom=max(.35,1.0+depth*.04)
    u=(xr/denom)*camera.scale*camera.focal_normalized
    v=(-zr/denom)*camera.scale*camera.focal_normalized
    ur=cos(ra)*u-sin(ra)*v; vr=sin(ra)*u+cos(ra)*v
    return camera.center_x+ur,camera.center_y+vr

def normalized_error(observed:list[NormalizedPoint], projected:list[tuple[float,float]])->float|None:
    if not observed or len(observed)!=len(projected): return None
    return sum(((a.x-b[0])**2+(a.y-b[1])**2)**.5 for a,b in zip(observed,projected))/len(observed)
