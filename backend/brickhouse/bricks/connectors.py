"""Conservative connector alignment for canonical rectangular LEGO bricks/plates.

Uses existing catalog dimensions. Rectangular stud-column overlap alone does NOT\nprove underside connector geometry: those contacts return UNKNOWN.
Unsupported families and nonstandard placements return UNKNOWN.
"""
from dataclasses import dataclass
from typing import Literal
from .brick_model import BrickModelPart
from .catalog import standard_orthogonal_definitions

Status = Literal["VALID", "INVALID", "UNKNOWN"]

@dataclass(frozen=True)
class ConnectionResult:
    status: Status
    interface_count: int
    reason: str

def _box(p: BrickModelPart):
    definition = standard_orthogonal_definitions().get(p.part_id)
    if definition is None or p.category not in ("brick", "plate"):
        return None
    w, d = definition.footprint(p.rotation_quarter_turns)
    h = definition.height_plates
    if p.width_studs is not None and p.length_studs is not None:
        dims = (p.width_studs, p.length_studs)
        if dims not in ((w,d),(definition.width_studs,definition.length_studs)):
            return None
    if p.height_plates is not None and p.height_plates != h:
        return None
    return (p.x_studs,p.y_studs,p.z_plates,p.x_studs+w,p.y_studs+d,p.z_plates+h)

def validate_connection(a: BrickModelPart,b: BrickModelPart) -> ConnectionResult:
    if a.placement_id == b.placement_id:
        return ConnectionResult("INVALID",0,"same-placement")
    A,B=_box(a),_box(b)
    if A is None or B is None:
        return ConnectionResult("UNKNOWN",0,"unsupported-or-inconsistent-catalog-geometry")
    dx=max(0,min(A[3],B[3])-max(A[0],B[0]))
    dy=max(0,min(A[4],B[4])-max(A[1],B[1]))
    dz=max(0,min(A[5],B[5])-max(A[2],B[2]))
    if dx*dy*dz:
        return ConnectionResult("INVALID",0,"solid-volume-collision")
    if not dx or not dy:
        return ConnectionResult("INVALID",0,"no-overlapping-stud-columns")
    if A[5]!=B[2] and B[5]!=A[2]:
        return ConnectionResult("INVALID",0,"no-vertical-connector-plane")
    # A rectangular grid of top studs and the standard underside engagement
    # of ordinary LEGO bricks/plates; internal tube coordinates not certified.
    return ConnectionResult("UNKNOWN",dx*dy,"stud-grid-aligned-but-underside-connector-geometry-unverified")
