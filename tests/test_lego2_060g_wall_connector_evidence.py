"""060G: LDraw-evidenced 1x6 <-> 1x8 interfaces on actual GUIDED-004.

Source geometry: 3008.dat -> 3008s01.dat; 3009.dat -> 3009s01.dat;
stud.dat/stud3.dat and the official 1x8 grouped primitives.
The fixture never asserts clutch strength, stability or insertability.
"""
from collections import Counter, defaultdict
from pathlib import Path

import pytest

from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.catalog import standard_orthogonal_definitions
from brickhouse.bricks.connectors import validate_connection
from brickhouse.bricks.physical_placement_gate import (
    Placement, build, build_geometrically, PhysicalPlacementGate,
)


def part(pid, kind, x=0, y=0, z=0, rotation=0, category="brick"):
    # model_construct permits deliberate unsupported semantic-category cases.
    return BrickModelPart.model_construct(
        placement_id=pid, part_id=kind, category=category,
        component="roof_support", x_studs=x, y_studs=y,
        z_plates=z, rotation_quarter_turns=rotation,
    )


@pytest.mark.parametrize("lower_kind,upper_kind", [
    ("BRICK_1X6", "BRICK_1X8"),
    ("BRICK_1X8", "BRICK_1X6"),
])
@pytest.mark.parametrize("rot", [0, 1])
@pytest.mark.parametrize("overlap", [1, 2, 3, 4, 5, 6])
def test_reviewed_orthogonal_stud_overlap_is_valid(lower_kind, upper_kind, rot, overlap):
    lower_n = int(lower_kind.split("X")[1])
    upper_n = int(upper_kind.split("X")[1])
    # Upper is to the left of lower by enough studs to leave EXACTLY
    # the requested 1..6 overlapping stud columns.
    longitudinal_offset = lower_n - overlap
    x, y = (longitudinal_offset, 0) if rot else (0, longitudinal_offset)
    lower = part("lower", lower_kind, rotation=rot)
    upper = part("upper", upper_kind, x=x, y=y, z=3, rotation=rot)
    res = validate_connection(lower, upper)
    assert (res.status, res.interface_count, res.reason) == (
        "VALID", overlap, "ldraw-3009-3008-reviewed-parallel-stud3-cavity"
    )


def test_official_ldraw_one_wide_stud3_clearance_for_each_1x6_1x8_stud_column():
    # Official LDraw: top stud radius 6; bottom stud3 radius 4;
    # cavity half-width 6; long-axis inner half-length n*10-4 LDU;
    # top stud locations (-n+1,-n+3,...,n-1)*10 LDU,
    # underside stud3 centres (-n+2,-n+4,...,n-2)*10 LDU.
    for n in (6, 8):
        top = [10 * k for k in range(-n + 1, n, 2)]
        underside = [10 * k for k in range(-n + 2, n - 1, 2)]
        assert len(top) == n and len(underside) == n - 1
        for stud_x in top:
            assert n * 10 - 4 - abs(stud_x) - 6 >= 0  # endwall
            assert 6 - 6 >= 0  # transverse internal sidewall
            assert min(abs(stud_x - t) - (6 + 4) for t in underside) >= 0


@pytest.mark.parametrize("lower,upper", [
    (part("a", "BRICK_1X6"), part("b", "BRICK_1X8", z=3, rotation=1)),
    (part("a", "BRICK_1X6", rotation=2), part("b", "BRICK_1X8", z=3, rotation=2)),
    (part("a", "BRICK_1X6", rotation=3), part("b", "BRICK_1X8", z=3, rotation=3)),
    (part("a", "BRICK_1X6", category="timber"), part("b", "BRICK_1X8", z=3)),
    (part("a", "BRICK_1X6"), part("b", "BRICK_1X8", category="timber", z=3)),
    (part("a", "BRICK_1X6"), part("b", "BRICK_1X6", z=3)),
    (part("a", "BRICK_1X8"), part("b", "BRICK_1X4", z=3)),
    (part("a", "PLATE_1X3"), part("b", "BRICK_1X3", z=1)),
])
def test_unreviewed_or_other_families_stay_unknown(lower, upper):
    assert validate_connection(lower, upper).status == "UNKNOWN"


@pytest.mark.parametrize("lower,upper", [
    (part("a", "BRICK_1X6"), part("b", "BRICK_1X8", z=2)),  # solid collision
    (part("a", "BRICK_1X6"), part("b", "BRICK_1X8", z=4)),  # wrong plane
    (part("a", "BRICK_1X6"), part("b", "BRICK_1X8", x=5, z=3)),  # no XY overlap
])
def test_incompatible_geometry_remains_invalid(lower, upper):
    assert validate_connection(lower, upper).status == "INVALID"


def test_strict_gate_accepts_reviewed_family_without_weakening_060b_060c():
    strict = build([
        Placement("BRICK_1X6", 0, 0, 0),
        Placement("BRICK_1X8", 0, 2, 3),
    ])
    assert isinstance(strict, PhysicalPlacementGate)
    assert strict.connector_validation == "REQUIRED_VALID"
    assert strict.physical_certification is False
    geom = build_geometrically([
        Placement("BRICK_1X6", 0, 0, 0),
        Placement("BRICK_1X8", 0, 2, 3),
    ])
    assert geom.connector_validation == "NOT_CHECKED"
    assert geom.validation_level == "GEOMETRY_ONLY"
    assert geom.physical_certification is False
    with pytest.raises(ValueError, match="UNKNOWN_CONNECTOR_SUPPORT"):
        build([
            Placement("PLATE_1X3", 0, 0, 0),
            Placement("BRICK_1X3", 0, 0, 1),
        ])


def test_actual_1890_part_guided004_wall_interfaces_and_support_delta():
    # ci.yml generates this official 1890-part artifact before pytest.
    source = Path("artifacts/lego2-guided-004/brick-model.json")
    if not source.is_file():
        pytest.skip("Actual GUIDED-004 export not available in this local checkout")
    model = BrickModel.model_validate_json(source.read_text(encoding="utf-8"))
    assert len(model.parts) == 1890
    catalog = standard_orthogonal_definitions()
    supported = []
    by_bottom = defaultdict(list)
    for p in model.parts:
        if p.part_id not in catalog or p.category not in ("brick", "plate", "timber"):
            continue
        supported.append(p)
        by_bottom[p.z_plates].append(p)

    classified = Counter()
    affected = Counter()
    all_upper = set()
    before_valid_uppers = set()
    after_valid_uppers = set()
    for lower in supported:
        lw, ll = catalog[lower.part_id].footprint(lower.rotation_quarter_turns)
        top_z = lower.z_plates + catalog[lower.part_id].height_plates
        for upper in by_bottom[top_z]:
            uw, ul = catalog[upper.part_id].footprint(upper.rotation_quarter_turns)
            dx = min(lower.x_studs + lw, upper.x_studs + uw) - max(lower.x_studs, upper.x_studs)
            dy = min(lower.y_studs + ll, upper.y_studs + ul) - max(lower.y_studs, upper.y_studs)
            if dx <= 0 or dy <= 0:
                continue
            result = validate_connection(lower, upper)
            classified[result.status] += 1
            all_upper.add(upper.placement_id)
            if result.status == "VALID":
                after_valid_uppers.add(upper.placement_id)
            if {lower.part_id, upper.part_id} == {"BRICK_1X6", "BRICK_1X8"}:
                assert (lower.category, upper.category) == ("brick", "brick")
                assert lower.rotation_quarter_turns == upper.rotation_quarter_turns
                assert lower.rotation_quarter_turns in (0, 1)
                assert result.status == "VALID"
                affected[(lower.part_id, upper.part_id)] += 1
            elif result.status == "VALID":
                before_valid_uppers.add(upper.placement_id)

    # 060F recorded exactly 1590 candidate connector-scope interfaces:
    # 1032 VALID / 558 UNKNOWN / 0 INVALID. Only this 162-pair family
    # is allowed to move from UNKNOWN to VALID.
    assert sum(classified.values()) == 1590
    assert affected == {
        ("BRICK_1X6", "BRICK_1X8"): 83,
        ("BRICK_1X8", "BRICK_1X6"): 79,
    }
    assert classified == {"VALID": 1194, "UNKNOWN": 396}
    assert len(all_upper) == 905
    assert len(all_upper - before_valid_uppers) == 277
    assert len(all_upper - after_valid_uppers) == 187
    assert len(after_valid_uppers - before_valid_uppers) == 90
