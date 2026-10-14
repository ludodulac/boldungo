"""Conservative connector alignment for canonical rectangular LEGO bricks/plates.

Uses existing catalog dimensions. Only the four LDraw-reviewed rectangular families can return VALID.\nVALID denotes modeled clutch-interface compatibility, not strength.
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
    if definition is None or p.category not in ("brick", "plate", "timber"):
        return None
    # GUIDED-004 timber is a semantic material; catalog geometry is unchanged.
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
    # Official LDraw geometries: 3005.dat underside cavity; 3008s01.dat
    # and 3666.dat underside stud3; 3007s01.dat central tube geometry.
    # Partial overlaps can engage via underside sidewalls/cavities.
    documented = {"BRICK_1X1", "BRICK_1X8", "BRICK_2X8", "PLATE_1X6"}
    # LDraw 3002s01.dat (2x3) and 2456.dat (2x6) show underside
    # stud4 tubes and surrounding sidewalls. Only certify the specifically
    # evidenced one-stud 1x1-post -> 2-wide-brick interface here; do NOT
    # promote arbitrary overlaps with these families.
    upper = b if A[5] == B[2] else a
    lower = a if upper is b else b
    if upper.part_id in {"BRICK_2X3", "BRICK_2X6"}:
        if lower.part_id == "BRICK_1X1" and dx == 1 and dy == 1:
            return ConnectionResult("VALID", 1, "ldraw-3002s01-or-2456-one-stud-sidewall-and-tube")
        return ConnectionResult("UNKNOWN", dx*dy, "upper-two-wide-interface-not-reviewed-for-this-lower-part")
    if a.part_id not in documented or b.part_id not in documented:
        return ConnectionResult("UNKNOWN",dx*dy,"underside-interface-not-documented-for-part")
    upper = b if A[5] == B[2] else a
    family = ("two-wide-tubes-and-sidewalls" if upper.part_id == "BRICK_2X8"
              else "one-wide-cavity" if upper.part_id == "BRICK_1X1"
              else "one-wide-stud3-and-sidewalls")
    return ConnectionResult("VALID",dx*dy,"ldraw-documented-"+family)
