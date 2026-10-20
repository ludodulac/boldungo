"""071: a ridge post is not anchored merely because it touches a wall top."""
from brickhouse.bricks.brick_model import BrickModelPart
from brickhouse.bricks.ridge_anchor_path_071 import trace_documented_wall_anchor
from brickhouse.bricks.ridge_structural_posts_070 import assess_structural_ridge_posts
from tests.bricks.test_ridge_structural_posts_070 import (
    anchored_wall, gable, house, roof, wall,
)


def support(pid, x, y, z):
    return BrickModelPart(
        placement_id=pid, part_id="BRICK_1X1",
        component="roof_support", category="brick",
        x_studs=x, y_studs=y, z_plates=z,
        rotation_quarter_turns=0,
    )


def test_isolated_wall_top_is_not_a_structural_anchor():
    m = gable(wall("floating-host", 40, 0, 111))
    saved = m.model_dump_json()
    result = assess_structural_ridge_posts(m)
    site = result["sites"][0]
    assert site["anchor_id"] == "floating-host"
    assert site["status"] == "UNKNOWN_UNANCHORED_RIDGE_POST"
    assert site["host_support_path"]["route_base_to_anchor"] == []
    assert site["post_parts"] == []
    assert site["post_connector_statuses"] == ["VALID", "VALID"]
    assert m.model_dump_json() == saved
    assert result["physical_certification"] == "NOT_CERTIFIED"


def test_complete_real_1x1_chain_to_z0_only_proves_nominal_interface():
    m = gable(*anchored_wall(40, 0, 111), wall("top", 40, 0, 111))
    before = m.model_dump_json()
    report = trace_documented_wall_anchor(m, next(p for p in m.parts
                                                   if p.placement_id == "top"))
    assert report["status"] == "DOCUMENTED_NOMINAL_WALL_STUD_PATH_TO_Z0"
    assert len(report["route_base_to_anchor"]) == 38
    assert report["route_base_to_anchor"][-1] == "top"
    assert report["ground_foundation"] == "UNKNOWN_NOT_CHECKED"
    assert report["mechanical_strength"] == "UNKNOWN_NOT_MEASURED"
    assert report["physical_certification"] == "NOT_CERTIFIED"
    assert before == m.model_dump_json()


def test_nominal_wall_overlap_cannot_bypass_unknown_lego_connector():
    m = gable(*anchored_wall(40, 0, 108),
              wall("undocumented-bridge", 40, 0, 108, "BRICK_1X4"),
              wall("host", 40, 0, 111))
    result = assess_structural_ridge_posts(m)
    site = result["sites"][0]
    assert site["anchor_id"] == "host"
    assert site["status"] == "UNKNOWN_UNANCHORED_RIDGE_POST"
    assert site["post_parts"] == []
    assert site["host_support_path"]["status"] == "UNKNOWN_NO_DOCUMENTED_WALL_LOAD_PATH"


def test_support_in_different_component_is_not_a_wall_foundation():
    m = gable(support("isolated-roof-support", 40, 0, 111))
    r = assess_structural_ridge_posts(m)
    site = r["sites"][0]
    assert site["status"] == "UNKNOWN_UNANCHORED_RIDGE_POST"
    assert site["host_support_path"]["status"] == "UNKNOWN_HOST_OUTSIDE_WALL_SUPPORT_DOMAIN"
    assert site["post_parts"] == []


def test_vertical_axis_rotated_gable_still_checks_the_wall_chain():
    m = house(roof("neg", "negative", 14, 2, 93, 1),
              roof("pos", "positive", 14, 2, 93, 1),
              *anchored_wall(14, 3, 87), wall("host", 14, 3, 87))
    r = assess_structural_ridge_posts(m)
    site = r["sites"][0]
    assert site["status"] == "UNKNOWN_LDRAW_LIBRARY_REQUIRED"
    assert site["host_support_path"]["status"] == "DOCUMENTED_NOMINAL_WALL_STUD_PATH_TO_Z0"
    assert site["post_to_lid"].startswith("UNKNOWN")
    assert site["lid_to_slopes"].startswith("UNKNOWN")
    assert site["structural_strength"] == "UNKNOWN_NOT_MEASURED"


def test_no_fake_ground_support_from_only_higher_wall_datum():
    m = gable(wall("raised-first", 40, 0, 108),
              wall("host", 40, 0, 111))
    r = assess_structural_ridge_posts(m)
    assert r["sites"][0]["status"] == "UNKNOWN_UNANCHORED_RIDGE_POST"
    assert r["sites"][0]["post_parts"] == []
