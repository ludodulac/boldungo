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


def _reviewed_guided004_30363_3008_eave(a: BrickModelPart, b: BrickModelPart):
    """060U: EXACT two GUIDED-004 30363/3008 interfaces, nominal geometry only.

    Official LDraw 30363.dat -> s/30363s01.dat:
      - roof underside cavity has sidewalls at local X=+/-16 LDU,
        front inside endwall Z=+6, far endwall Z=-66;
      - underside hollow tube axes at local (X=0,Z=-10,-30,-50), with
        8-LDU outside radii (stud4a.dat / stud4s.dat);
      - a roof inner ceiling is at local Y=4 around Z=0, increasing
        toward the lower, sloped end (well above the inserted studs).
      - an internal web around Z=[-42,-34] is outside these interfaces.
    Official LDraw 3008.dat -> s/3008s01.dat -> stug-1x8.dat:
      eight top studs, radius 6 LDU, extending 4 LDU above the top.

    For these exact THREE stud centres, the roof-local underside positions
    are A: (X=10,Z=-20),(X=10,Z=0), B: (X=-10,Z=-20).
    All three are tangent to the cavity sidewall (0 nominal clearance).
    The (10,0) stud is also tangent to the front inside endwall.
    Closest tube's horizontal outside clearance is sqrt(200)-14 > 0 LDU.
    The stud height lies in the open cavity at roof-local Y=20..24;
    no web lies within their radius-6 footprints.

    No finite clearance allowance, insertion path, clutch force, or real
    stability is claimed. All other roof joints remain UNKNOWN.
    """
    from .geometry_adapter import CANONICAL_LDRAW_PARTS, _slope_transform
    from .lego30363_mechanics_034 import _30363_BBOX_ONLY

    roof, wall = (a, b) if a.part_id == "BRICK_SLOPED_18_4X2" else (b, a)
    if (roof.placement_id != "roof-000002"
            or roof.part_id != "BRICK_SLOPED_18_4X2"
            or roof.category != "roof_tile" or roof.component != "roof"
            or roof.roof_side != "negative"
            or (roof.x_studs, roof.y_studs, roof.z_plates,
                roof.rotation_quarter_turns) != (14, 2, 93, 0)):
        return None
    walls = {
        "wall-000699": ((16, 2, 90, 1), {(16, 2), (17, 2)}, {(10, -20), (10, 0)}),
        "wall-000715": ((16, 3, 90, 0), {(16, 3)}, {(-10, -20)}),
    }
    if wall.placement_id not in walls or wall.part_id != "BRICK_1X8":
        return None
    if wall.category != "brick" or wall.component != "wall":
        return None
    pose, expected_cells, expected_local = walls[wall.placement_id]
    if (wall.x_studs, wall.y_studs, wall.z_plates,
            wall.rotation_quarter_turns) != pose:
        return None
    # Reject inconsistent metadata, never silently reuse a known placement ID.
    for part, expected in ((roof, (4, 2, 3)), (wall, (1, 8, 3))):
        # The BrickModel metadata may be absent or nominal/unrotated.
        metadata = (part.width_studs, part.length_studs, part.height_plates)
        if any(value is not None and value != nominal
               for value, nominal in zip(metadata, expected)):
            return None

    definition = standard_orthogonal_definitions()["BRICK_1X8"]
    width, depth = definition.footprint(wall.rotation_quarter_turns)
    roof_cells = {(x, y) for x in range(14, 18) for y in range(2, 4)}
    wall_cells = {(x, y)
                  for x in range(wall.x_studs, wall.x_studs + width)
                  for y in range(wall.y_studs, wall.y_studs + depth)}
    engaged_cells = wall_cells & roof_cells
    if engaged_cells != expected_cells or wall.z_plates + 3 != roof.z_plates:
        return None

    transform = _slope_transform(
        roof, CANONICAL_LDRAW_PARTS[roof.part_id], _30363_BBOX_ONLY
    )
    rotation = transform.matrix
    # True 30363 canonical orientation, not the old 034 2x4 grid.
    if (tuple(rotation[0]), tuple(rotation[1]), tuple(rotation[2])) != (
        (0.0, 0.0, 1.0, 350.0),
        (0.0, 1.0, 0.0, -768.0),
        (-1.0, 0.0, 0.0, 60.0),
    ):
        return None

    locals_found = set()
    for x, y in engaged_cells:
        # World LDraw coordinates: X=canonical X*20, Z=canonical Y*20,
        # world Y negative upward. Use inverse of the existing R matrix.
        world = ((x + 0.5) * 20.0,
                 -roof.z_plates * 8.0,
                 (y + 0.5) * 20.0)
        delta = tuple(world[i] - rotation[i][3] for i in range(3))
        lx, ly, lz = (
            sum(rotation[i][j] * delta[i] for i in range(3))
            for j in range(3)
        )
        # The wall stud has a 4-LDU vertical span, Y=20..24
        # relative to this roof. Only this insertion-free final pose
        # is assessed, never the vertical approach trajectory.
        stud_tip_y = ly - 4.0
        if abs(ly - 24.0) > 1e-6 or abs(stud_tip_y - 20.0) > 1e-6:
            return None
        if min(
            16.0 - abs(lx) - 6.0,  # internal left/right sidewalls
            6.0 - lz - 6.0,       # high-end cavity wall at Z=+6
            lz - 6.0 + 66.0,      # low-end cavity wall at Z=-66
        ) < -1e-6:
            return None
        if min(math.hypot(lx, lz - tube_z) - 14.0
               for tube_z in (-10.0, -30.0, -50.0)) <= 0.0:
            return None
        # For Z=-20 or Z=0 the roof's underside is well above the
        # inserted stud tip; internal web Z=-42..-34 cannot intersect.
        if not any(abs(lx - xx) < 1e-6 and abs(lz - zz) < 1e-6
                   for xx, zz in expected_local):
            return None
        locals_found.add((round(lx), round(lz)))
    if locals_found != expected_local:
        return None
    return ConnectionResult(
        "VALID", len(engaged_cells),
        "ldraw-30363-3008-guided004-eave-reviewed-sidewall-tube",
    )


def validate_connection(a: BrickModelPart,b: BrickModelPart) -> ConnectionResult:
    if a.placement_id == b.placement_id:
        return ConnectionResult("INVALID",0,"same-placement")
    reviewed_eave = _reviewed_guided004_30363_3008_eave(a, b)
    if reviewed_eave is not None:
        return reviewed_eave
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
