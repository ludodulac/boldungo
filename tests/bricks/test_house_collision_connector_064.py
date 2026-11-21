"""Generic house, real LDraw, no fabricated clutch certificates (missions 1+2)."""
import json
from pathlib import Path

import pytest

from lego_geometry_engine import LDrawLibrary
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.connector_audit_064 import audit_orthogonal_connections
from brickhouse.bricks.roof_host_mesh_064 import roof_host_candidates, check_roof_host_mesh
from brickhouse.bricks.roof_mesh_preflight import preflight_roof_mesh

FIXTURE = Path("lego_geometry_engine/tests/fixtures/ldraw")


def wall(pid, x, y, z, part_id="BRICK_1X1"):
    return BrickModelPart(placement_id=pid, part_id=part_id, category="brick",
                          component="wall", facade="front", x_studs=x,
                          y_studs=y, z_plates=z, rotation_quarter_turns=0)


def roof(pid, x, y, z, part_id="BRICK_SLOPED_45_2X4", side="negative"):
    return BrickModelPart(placement_id=pid, part_id=part_id, category="roof_tile",
                          component="roof", roof_side=side, x_studs=x,
                          y_studs=y, z_plates=z, rotation_quarter_turns=0)


def house(name, *parts):
    return BrickModel(building_id=name, volume_id="main",
                      width_studs=30, depth_studs=30, height_plates=30,
                      parts=list(parts))


def test_real_ldraw_roof_to_wall_3d_is_evaluated_not_certified():
    m = house("different-house", roof("r", 0, 0, 6), wall("w", 0, 0, 3))
    rows, truncated, omitted = roof_host_candidates(m)
    assert [(r.placement_id, w.placement_id) for r, w in rows] == [("r", "w")]
    assert not truncated and not omitted
    result = check_roof_host_mesh(m, LDrawLibrary(FIXTURE))
    assert result["pairs_examined"] == 1
    pair = result["pairs"][0]
    assert pair["mesh_relation"] in ("COLLISION", "CONTACT", "SEPARATED")
    assert pair["status"] != "UNKNOWN_GEOMETRY_UNAVAILABLE"
    assert pair["connector_status"] == "UNKNOWN_UNVERIFIED_ROOF_UNDERSIDE"
    assert result["physical_certification"] == "NOT_CERTIFIED"


def test_real_ldraw_opposing_slopes_checked_by_existing_mesh_engine():
    m = house("second-house", roof("neg", 0, 0, 6),
              roof("pos", 1, 0, 6, side="positive"))
    report = preflight_roof_mesh(m, LDrawLibrary(FIXTURE))
    assert report["pairs_examined"] == 1
    assert report["pairs"][0]["mesh_relation"] in ("COLLISION", "CONTACT", "SEPARATED")
    assert report["physical_certification"] == "NOT_CERTIFIED"


def test_nominal_orthogonal_stud_clutch_vs_sidewalls():
    m = house("brick-house", wall("base", 0, 0, 0),
              wall("top", 0, 0, 3),
              wall("beside", 1, 0, 0))
    result = audit_orthogonal_connections(m)
    assert result["candidate_interfaces"] == 1
    assert result["checked_interfaces"] == 1
    assert result["status_counts"] == {"VALID": 1}
    assert result["examples"][0]["lower"] == "base"
    assert result["examples"][0]["upper"] == "top"
    assert result["physical_certification"] == "NOT_CERTIFIED"


def test_unreviewed_regular_interface_must_remain_unknown():
    m = house("unreviewed", wall("lower", 0, 0, 0),
              wall("upper", 0, 0, 3, part_id="BRICK_1X4"))
    result = audit_orthogonal_connections(m)
    assert result["status_counts"] == {"UNKNOWN": 1}
    assert result["candidate_interfaces"] == 1


def test_slope_underface_never_promoted_to_stud_clutch():
    m = house("slope-support", roof("roof", 0, 0, 6),
              wall("host", 0, 0, 3))
    r = audit_orthogonal_connections(m)
    assert r["candidate_interfaces"] == 0
    assert r["slope_underside_interfaces"].startswith("UNKNOWN")
    no_lib = check_roof_host_mesh(m, None)
    assert no_lib["pairs"][0]["status"] == "UNKNOWN_LDRAW_LIBRARY_NOT_PROVIDED"
    assert no_lib["physical_certification"] == "NOT_CERTIFIED"


def test_mono_pitch_geometry_remains_unknown_if_transform_not_supported():
    m = house("shed", roof("shed-roof", 0, 0, 6, side="slope"),
              wall("host", 0, 0, 3))
    evidence = check_roof_host_mesh(m, LDrawLibrary(FIXTURE))
    assert evidence["pairs"][0]["status"] == "UNKNOWN_GEOMETRY_UNAVAILABLE"


def test_bounded_discovery_and_processing_visible_in_output():
    m = house("bounded", roof("r", 0, 0, 6),
              wall("w1", 0, 0, 3), wall("w2", 1, 0, 3))
    r = check_roof_host_mesh(m, LDrawLibrary(FIXTURE), max_pairs=1)
    assert r["candidate_pairs"] == 2 and r["examination_truncated"]
    assert r["pairs_examined"] == 1
    _, truncated, _ = roof_host_candidates(m, max_candidates=1)
    assert truncated
    with pytest.raises(ValueError, match="positive"):
        audit_orthogonal_connections(m, max_interfaces=0)


def test_real_1890_part_house_connections_not_falsely_certified():
    path = Path("artifacts/lego2-guided-004/brick-model.json")
    if not path.is_file():
        pytest.skip("real canonical export missing in this checkout")
    model = BrickModel.model_validate_json(path.read_text())
    assert len(model.parts) == 1890
    hosts, truncated, _ = roof_host_candidates(model)
    expected = {("roof-000002", "wall-000699"),
                ("roof-000002", "wall-000715")}
    found = {(a.placement_id, b.placement_id) for a, b in hosts}
    assert expected <= found
    assert not truncated
    r = audit_orthogonal_connections(model)
    assert not r["examination_truncated"]
    assert r["physical_certification"] == "NOT_CERTIFIED"
