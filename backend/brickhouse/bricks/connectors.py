"""Conservative connector alignment for canonical rectangular LEGO bricks/plates.

Uses existing catalog dimensions. The documented LDraw-reviewed interfaces can return VALID.\nVALID denotes modeled clutch-interface compatibility, not strength.
Unsupported families and nonstandard placements return UNKNOWN.
"""
import math
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


def _reviewed_plate_1x3_brick_2x8_edge(lower: BrickModelPart, upper: BrickModelPart) -> bool:
    """Narrow, nominal LDraw-compatible edge-stud/sidewall interfaces.

    Official 3623s01.dat/3007s01.dat: plate upper studs radius 6 LDU;
    brick internal sidewall at transverse +/-16 LDU, endwall +/-76,
    seven interior tubes (radius 8) at longitudinal -60..60 every 20.
    One plate row x one of the two brick rows: stud center transverse
    +/-10, touching the inside sidewall. Near the two brick ends, the
    nearest tube is sqrt(10**2+10**2)-14 > 0 LDU clear. The 4-LDU-tall
    plate studs fit within the brick underside cavity (y=20..24 LDU);
    3007s01 transverse reinforcement ribs stop at y=18.5 LDU.
    This establishes *modeled geometry* only, never mechanical strength.

    Deliberately do NOT generalize to every PLATE_1X3 joint, rotation,
    or interior placement: those remain UNKNOWN pending further review.
    """
    if (lower.part_id != "PLATE_1X3" or lower.category != "plate"
            or upper.part_id != "BRICK_2X8"
            or upper.rotation_quarter_turns != 0
            or lower.rotation_quarter_turns != 0
            or lower.x_studs not in (upper.x_studs, upper.x_studs + 1)):
        return False
    first = max(lower.y_studs, upper.y_studs)
    last = min(lower.y_studs + 3, upper.y_studs + 8)
    indices = [y - upper.y_studs for y in range(first, last)]
    if not indices or len(indices) > 2:
        return False
    if not (set(indices) <= {0, 1} or set(indices) <= {6, 7}):
        return False
    transverse = -10 if lower.x_studs == upper.x_studs else 10
    for i in indices:
        longitudinal = -70 + 20 * i
        side_clearance = 16 - (abs(transverse) + 6)
        end_clearance = 76 - (abs(longitudinal) + 6)
        tube_clearance = min(
            math.hypot(transverse, longitudinal - tube) - 14
            for tube in range(-60, 61, 20)
        )
        if side_clearance != 0 or end_clearance < 0 or tube_clearance <= 0:
            return False
    return True

def _reviewed_brick_1x6_1x8_parallel(lower: BrickModelPart, upper: BrickModelPart,
                                    dx: int, dy: int) -> bool:
    """Evidence-specific 1-wide 3009.dat / 3008.dat stacked interfaces.

    Official LDraw geometry (NOT a strength/clutch or insertion certificate):
      3009.dat -> s/3009s01.dat: six top studs at +/-10,30,50 LDU,
      five underside stud3 centres at -40,-20,0,20,40 LDU;
      3008.dat -> s/3008s01.dat -> stug3-1x7.dat / stug-1x8.dat:
      eight top studs at +/-10,30,50,70 and seven underside stud3
      centres at -60,-40,-20,0,20,40,60 LDU.
    stud.dat radius 6, stud3.dat radius 4. The 1-wide internal cavity
    has sidewalls at transverse +/-6 LDU and endwalls at +/- (10*n-4);
    stud centres are longitudinal +/- (10*n-10), giving >=6 LDU end
    clearance and 10 LDU stud-to-stud3 separation. There is nominal
    tangency, without a modeled volumetric interference, for each aligned
    stud of an orthogonal same-axis overlap. All 162 GUIDED-004 interfaces
    use equal rotations 0/0 or 1/1, overlaps of 1 to 6 stud columns.

    Sources: https://library.ldraw.org/library/official/parts/3009.dat
             https://library.ldraw.org/library/official/parts/s/3009s01.dat
             https://library.ldraw.org/library/official/parts/3008.dat
             https://library.ldraw.org/library/official/parts/s/3008s01.dat
             https://library.ldraw.org/library/official/p/stud.dat
             https://library.ldraw.org/library/official/p/stud3.dat

    Rotations 2/3, perpendicular axes and all other part families stay
    outside THIS reviewed configuration, even when geometry overlaps.
    """
    if ({lower.part_id, upper.part_id} != {"BRICK_1X6", "BRICK_1X8"}
            or lower.category != "brick" or upper.category != "brick"
            or lower.rotation_quarter_turns != upper.rotation_quarter_turns
            or upper.rotation_quarter_turns not in (0, 1)):
        return False
    if upper.rotation_quarter_turns == 0:
        # Unrotated 1xn extends along Y, with the same X stud row.
        return lower.x_studs == upper.x_studs and dx == 1 and 1 <= dy <= 6
    # Quarter-turn 1 extends along X, with the same Y stud row.
    return lower.y_studs == upper.y_studs and dy == 1 and 1 <= dx <= 6


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
    if _reviewed_plate_1x3_brick_2x8_edge(lower, upper):
        return ConnectionResult("VALID", dx * dy, "ldraw-3623-3007-reviewed-edge-stud-sidewall")
    if _reviewed_brick_1x6_1x8_parallel(lower, upper, dx, dy):
        return ConnectionResult(
            "VALID", dx * dy, "ldraw-3009-3008-reviewed-parallel-stud3-cavity"
        )
    if a.part_id not in documented or b.part_id not in documented:
        return ConnectionResult("UNKNOWN",dx*dy,"underside-interface-not-documented-for-part")
    upper = b if A[5] == B[2] else a
    family = ("two-wide-tubes-and-sidewalls" if upper.part_id == "BRICK_2X8"
              else "one-wide-cavity" if upper.part_id == "BRICK_1X1"
              else "one-wide-stud3-and-sidewalls")
    return ConnectionResult("VALID",dx*dy,"ldraw-documented-"+family)
