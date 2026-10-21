"""LEGO2-082: candidate design stops BEFORE unsupported roof assembly."""
from pathlib import Path

import pytest

from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.connector_first_design_082 import (
    describe_interfaces, screen_connector_first_candidate,
)


def brick(pid, part_id, x=5, y=7, z=0, rotation=0):
    return BrickModelPart(
        placement_id=pid, part_id=part_id, category="brick",
        component="roof_support", x_studs=x, y_studs=y,
        z_plates=z, rotation_quarter_turns=rotation,
    )


def roof(pid, side, x, y, z, rotation=0, part_id="BRICK_SLOPED_18_4X2"):
    return BrickModelPart(
        placement_id=pid, part_id=part_id,
        category="ridge_tile" if side == "ridge" else "roof_tile",
        component="roof", roof_side=side,
        x_studs=x, y_studs=y, z_plates=z,
        rotation_quarter_turns=rotation,
    )


def test_1x1_to_3002_nominal_interface_is_eligible_but_not_certified():
    post = brick("post", "BRICK_1X1")
    head = brick("head", "BRICK_2X3", z=3)
    before = (post.model_dump_json(), head.model_dump_json())
    report = screen_connector_first_candidate([post, head], [("post", "head")])
    assert report["decision"] == "ELIGIBLE_FOR_FURTHER_DESIGN_CHECKS"
    assert report["documented_nominal_connections"] == 1
    assert report["missing_gates"][0] == "NON_CONNECTOR_BODY_CLEARANCE"
    assert report["physical_certification"] == "NOT_CERTIFIED"
    assert before == (post.model_dump_json(), head.model_dump_json())


def test_duplicated_top_studs_are_rejected_before_any_mesh_analysis():
    a = brick("a", "BRICK_1X1", x=10, y=5, z=9)
    b = brick("b", "BRICK_1X1", x=10, y=5, z=9)
    r = screen_connector_first_candidate([a, b], [("a", "b")])
    assert r["decision"] == "REJECTED_DUPLICATE_STUD_MATERIAL"
    assert r["duplicated_top_studs"] == [{"cell": [10, 5, 12], "owners": ["a", "b"]}]


@pytest.mark.parametrize("rotation", [0, 1])
def test_documented_30363_top_stud_sites_are_not_generic_footprint(rotation):
    a = roof("slope", "negative", 38, 2, 117, rotation)
    profile = describe_interfaces(a)
    assert len(profile.top_studs) == 2
    assert all(x.evidence == "LDRAW_REVIEWED" for x in profile.top_studs)
    assert all("lego30363_mechanics_034" in x.source for x in profile.top_studs)
    assert not profile.possible_receivers
    assert "UNDERSIDE_UNVERIFIED" in profile.source_note


@pytest.mark.parametrize("rotation", [0, 1])
def test_3005_and_slope_claiming_same_stud_is_explicit_rejection(rotation):
    slope = roof("slope", "negative", 38, 2, 117, rotation)
    point = describe_interfaces(slope).top_studs[0].position
    post = brick("post", "BRICK_1X1", point[0], point[1], point[2] - 3)
    r = screen_connector_first_candidate([post, slope], [("post", "slope")])
    assert r["decision"] == "REJECTED_DUPLICATE_STUD_MATERIAL"
    assert r["duplicated_top_studs"][0]["cell"] == list(point)


@pytest.mark.parametrize("rotation", [0, 1])
def test_26603_two_real_tube_axes_are_not_fake_six_individual_mates(rotation):
    tile = roof("cap", "ridge", 15, 20, 120, rotation, "TILE_2X3")
    profile = describe_interfaces(tile)
    assert len(profile.possible_receivers) == 2
    assert all(x.kind == "TUBE_AXIS" for x in profile.possible_receivers)
    assert all(x.evidence == "LDRAW_REVIEWED" for x in profile.possible_receivers)
    assert profile.has_documented_mating_receiver is False
    assert not profile.top_studs


def test_known_3002_to_26603_nominal_alignment_remains_rejected_until_reviewed_joint():
    head = brick("head", "BRICK_2X3", x=10, y=10, z=0)
    tile = roof("cover", "ridge", 10, 10, 3, 0, "TILE_2X3")
    report = screen_connector_first_candidate([head, tile], [("head", "cover")])
    assert report["decision"] == "REJECTED_UNDOCUMENTED_OR_INCOMPATIBLE_JOINT"
    assert report["blocked_connections"][0]["design_gate"] == "REJECTED_UNDOCUMENTED_INTERFACE"
    assert report["physical_certification"] == "NOT_CERTIFIED"


def test_non_documented_slope_cannot_be_selected_as_a_receiver():
    upper = roof("slope", "positive", 12, 9, 3)
    lower = brick("post", "BRICK_1X1", 12, 9, 0)
    report = screen_connector_first_candidate([lower, upper], [("post", "slope")])
    assert report["decision"] == "REJECTED_UNDOCUMENTED_OR_INCOMPATIBLE_JOINT"
    assert report["blocked_connections"][0]["design_gate"] == "REJECTED_UNDOCUMENTED_INTERFACE"


def test_missing_id_and_empty_required_connections_fail_closed():
    post = brick("p", "BRICK_1X1")
    assert screen_connector_first_candidate([post], [])["decision"] == "REJECTED_NO_REQUIRED_CONNECTIONS"
    r = screen_connector_first_candidate([post], [("p", "not-there")])
    assert r["blocked_connections"][0]["design_gate"] == "REJECTED_UNKNOWN_PART_ID"


def test_unreviewed_roof_family_must_not_inherit_stud_rules():
    slope = roof("other", "negative", 10, 10, 0,
                 part_id="BRICK_SLOPED_33_3X2")
    profile = describe_interfaces(slope)
    assert not profile.top_studs and not profile.possible_receivers
    assert profile.source_note.startswith("ROOF_FAMILY_CONNECTORS_NOT_DOCUMENTED")


def test_rotated_standard_piece_gets_rotated_stud_sites():
    p = brick("rotated", "BRICK_1X2", 10, 20, 3, rotation=1)
    sites = describe_interfaces(p).top_studs
    assert {x.position for x in sites} == {(10, 20, 6), (11, 20, 6)}


def test_duplicate_ids_and_unbounded_designs_are_rejected():
    p = brick("dup", "BRICK_1X1")
    with pytest.raises(ValueError, match="duplicate"):
        screen_connector_first_candidate([p, p], [("dup", "dup")])
    with pytest.raises(ValueError, match="budget"):
        screen_connector_first_candidate([p], [], max_parts=0)


def test_guided004_canonical_1890_parts_remain_byte_for_byte_unchanged():
    path = Path("artifacts/lego2-guided-004/brick-model.json")
    if not path.is_file():
        pytest.skip("real canonical GUIDED-004 export is not in this checkout")
    model = BrickModel.model_validate_json(path.read_text())
    before = model.model_dump_json()
    assert len(model.parts) == 1890
    roofs = [p for p in model.parts if p.part_id == "BRICK_SLOPED_18_4X2"][:2]
    assert len(roofs) == 2
    r = screen_connector_first_candidate(roofs, [(roofs[0].placement_id, roofs[1].placement_id)])
    assert r["decision"] != "ELIGIBLE_FOR_FURTHER_DESIGN_CHECKS"
    assert r["model_mutated"] is False
    assert model.model_dump_json() == before
