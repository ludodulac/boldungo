"""074: mechanically conservative 3002-26603 stud/tube interface gate."""
from pathlib import Path

import pytest
from lego_geometry_engine import LDrawLibrary

from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.ridge_clutch_verifier_074 import validate_3002_26603_clutch
from brickhouse.bricks.ridge_cap_adapter_072 import assess_ridge_cap_adapters


def brick(x=5, y=7, z=6, turns=0, part_id="BRICK_2X3", pid="head"):
    return BrickModelPart(
        placement_id=pid, part_id=part_id, category="brick",
        component="roof_support", x_studs=x, y_studs=y,
        z_plates=z, rotation_quarter_turns=turns,
    )


def tile(x=5, y=7, z=9, turns=0, part_id="TILE_2X3"):
    return BrickModelPart(
        placement_id="tile", part_id=part_id, category="ridge_tile",
        component="roof", roof_side="ridge",
        x_studs=x, y_studs=y, z_plates=z,
        rotation_quarter_turns=turns,
    )


@pytest.mark.parametrize("turns,x,y,z", [
    (0, 2, 6, 3), (1, 11, 8, 18),
    (2, 4, 12, 48), (3, 23, 14, 90),
])
def test_all_rotations_match_six_studs_two_tubes_without_fake_mechanical_valid(turns, x, y, z):
    head, lid = brick(x, y, z, turns), tile(x, y, z + 3, turns)
    before = (head.model_dump_json(), lid.model_dump_json())
    report = validate_3002_26603_clutch(head, lid)
    assert report["status"] == "UNKNOWN"
    assert report["nominal_layout_status"] == "VALID"
    assert report["nominal_geometry"] == "NOMINAL_LDRAW_STUD_AND_TUBE_LAYOUT_ONLY"
    assert report["stud_tube_clutch"].startswith("UNKNOWN")
    assert report["reason"] == "LDRAW_LIBRARY_NOT_PROVIDED"
    assert report["physical_certification"] == "NOT_CERTIFIED"
    assert report["model_mutated"] is False
    assert (head.model_dump_json(), lid.model_dump_json()) == before


@pytest.mark.parametrize("change", [
    {"z": 11}, {"x": 6}, {"y": 8},
])
def test_reject_incompatible_full_seat_configuration(change):
    lid = tile(**change)
    r = validate_3002_26603_clutch(brick(), lid)
    assert r["status"] == "INVALID"
    assert r["nominal_layout_status"] == "INVALID"
    assert r["reason"] == "INCOMPATIBLE_FULL_SEAT_PLACEMENT"
    assert r["checks_performed"] == 0
    assert r["physical_certification"] == "NOT_CERTIFIED"


def test_unreviewed_family_and_relative_rotation_are_unknown_not_invalid():
    assert validate_3002_26603_clutch(
        brick(), tile(part_id="TILE_2X4"))["status"] == "UNKNOWN"
    assert validate_3002_26603_clutch(
        brick(), tile(turns=1))["status"] == "UNKNOWN"


def test_real_fixture_ldraw_missing_official_pair_cannot_certify_interface():
    library = LDrawLibrary(Path("lego_geometry_engine/tests/fixtures/ldraw"))
    report = validate_3002_26603_clutch(brick(), tile(), library)
    assert report["status"] == "UNKNOWN"
    assert len(report["discrete_insertion_checks"]) == 4
    assert [r["lift_plates"] for r in report["discrete_insertion_checks"]] == [3, 2, 1, 0]
    assert report["checks_performed"] == 4
    assert report["reason"] == "INCOMPLETE_LDRAW_PART_GEOMETRY"
    assert report["mesh_at_seated_height"] == "UNKNOWN_GEOMETRY_UNAVAILABLE"
    assert report["physical_certification"] == "NOT_CERTIFIED"


def test_bounded_discrete_insertion_reuses_existing_pair_check(monkeypatch):
    called = []
    def fake_pair(a, b, library, cache, relation_cache):
        called.append((a.placement_id, a.z_plates, b.placement_id))
        return {"part_a": a.placement_id, "part_b": b.placement_id,
                "status": "MESH_CONTACT_REVIEW_REQUIRED",
                "mesh_relation": "CONTACT"}
    monkeypatch.setattr("brickhouse.bricks.ridge_clutch_verifier_074._pair", fake_pair)
    h, c = brick(), tile()
    before = (h.model_dump_json(), c.model_dump_json())
    r = validate_3002_26603_clutch(h, c, object(), lift_plates=(4, 2, 0))
    assert r["status"] == "UNKNOWN"
    assert r["reason"] == "DISCRETE_MESH_SCREEN_DONE_PHYSICAL_CLUTCH_UNPROVEN"
    assert [z for _, z, _ in called] == [13, 11, 9]
    assert len({a for a, _, _ in called}) == 3
    assert r["mesh_at_seated_height"] == "MESH_CONTACT_REVIEW_REQUIRED"
    assert r["checks_performed"] == 3
    assert (h.model_dump_json(), c.model_dump_json()) == before


def test_report_does_not_hide_intersection_as_valid_clutch(monkeypatch):
    def collision(a, b, *args):
        return {"part_a": a.placement_id, "part_b": b.placement_id,
                "status": "MESH_INTERSECTION_REVIEW_REQUIRED", "mesh_relation": "COLLISION"}
    monkeypatch.setattr("brickhouse.bricks.ridge_clutch_verifier_074._pair", collision)
    report = validate_3002_26603_clutch(brick(), tile(), object())
    assert report["reason"] == "MESH_INTERFERENCE_NEEDS_CONNECTOR_AWARE_REVIEW"
    assert report["status"] == "UNKNOWN"
    assert report["physical_certification"] == "NOT_CERTIFIED"


def test_nearby_parts_are_scanned_and_budget_truncation_is_reported(monkeypatch):
    def separated(a, b, *args):
        return {"part_a": a.placement_id, "part_b": b.placement_id,
                "status": "MESH_SEPARATED", "mesh_relation": "SEPARATED"}
    monkeypatch.setattr("brickhouse.bricks.ridge_clutch_verifier_074._pair", separated)
    report = validate_3002_26603_clutch(
        brick(), tile(), object(), surrounding=[brick(pid="obstruction", z=9)],
        max_pair_checks=3)
    assert report["status"] == "UNKNOWN"
    assert report["reason"] == "INCOMPLETE_LDRAW_PAIR_BUDGET"
    assert report["checks_performed"] == 3
    assert len(report["missing_or_skipped_checks"]) == 5
    assert report["mesh_at_seated_height"] == "UNKNOWN_NOT_CHECKED"


def test_duplicate_surroundings_fail_closed():
    parts = [brick(pid="x"), brick(pid="x")]
    report = validate_3002_26603_clutch(brick(), tile(), object(), surrounding=parts)
    assert report["reason"] == "AMBIGUOUS_DUPLICATE_SURROUNDING_IDS"
    assert report["status"] == "UNKNOWN"


@pytest.mark.parametrize("steps", [
    (), (2, 1), (0, 1, 0), (1, 1, 0), (-1, 0), (1.5, 0), tuple(range(12, -1, -1)),
])
def test_invalid_discrete_sweep_configuration_is_rejected(steps):
    with pytest.raises(ValueError):
        validate_3002_26603_clutch(brick(), tile(), lift_plates=steps)
    with pytest.raises(ValueError):
        validate_3002_26603_clutch(brick(), tile(), max_pair_checks=0)


def _roof(pid, side, x, y, z, turns=0):
    return BrickModelPart(
        placement_id=pid, part_id="BRICK_SLOPED_18_4X2",
        category="roof_tile", component="roof", roof_side=side,
        x_studs=x, y_studs=y, z_plates=z,
        rotation_quarter_turns=turns,
    )


def _wall(pid, x, y, z):
    return BrickModelPart(
        placement_id=pid, part_id="BRICK_1X1",
        category="brick", component="wall", facade="front",
        x_studs=x, y_studs=y, z_plates=z, rotation_quarter_turns=0,
    )


def _house(shift=0, anchored=True, turns=0):
    if turns == 0:
        locs = ((38 + shift, 2), (39 + shift, 2))
        host_x, host_y, z, host_z = (40 + shift, 2, 117, 111)
    else:
        locs = ((14 + shift, 2), (14 + shift, 2))
        host_x, host_y, z, host_z = (14 + shift, 3, 93, 87)
    return BrickModel(
        building_id="another-roof", volume_id="main",
        width_studs=110, depth_studs=110, height_plates=180,
        parts=[
            _roof("left", "negative", *locs[0], z, turns),
            _roof("right", "positive", *locs[1], z, turns),
            *[_wall(f"host-{i}", host_x, host_y, i)
              for i in (range(0, host_z+1, 3) if anchored else [host_z])],
        ],
    )


def test_adapter_reports_explicit_unknown_clutch_and_preserves_second_house():
    m = _house(shift=11)
    saved = m.model_dump_json()
    r = assess_ridge_cap_adapters(m)
    assert r["sites"][0]["upper_clutch_review"]["status"] == "UNKNOWN"
    assert r["sites"][0]["upper_clutch_review"]["nominal_layout_status"] == "VALID"
    assert r["sites"][0]["upper_clutch_review"]["stud_tube_clutch"].startswith("UNKNOWN")
    assert r["physical_certification"] == "NOT_CERTIFIED"
    assert m.model_dump_json() == saved


def test_second_orientation_and_floating_host_stay_unvalidated():
    for m in (_house(turns=1), _house(shift=22, anchored=False)):
        r = assess_ridge_cap_adapters(m)
        assert r["sites"][0]["headpiece"] is None
        assert r["sites"][0]["upper_clutch_review"]["status"] == "UNKNOWN"
        assert r["physical_certification"] == "NOT_CERTIFIED"


def test_canonical_1890_bricks_remain_identical():
    p = Path("artifacts/lego2-guided-004/brick-model.json")
    if not p.is_file():
        pytest.skip("canonical model not present in local checkout")
    m = BrickModel.model_validate_json(p.read_text(encoding="utf-8"))
    assert len(m.parts) == 1890
    original = m.model_dump_json()
    r = assess_ridge_cap_adapters(m, max_sites=1)
    assert r["original_part_count"] == 1890
    assert r["model_mutated"] is False
    assert r["physical_certification"] == "NOT_CERTIFIED"
    assert m.model_dump_json() == original
