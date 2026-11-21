"""LEGO2-073: real official 3002/26603 connector layout, never strength."""
import pytest
from pathlib import Path
from lego_geometry_engine import LDrawLibrary

from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.ridge_cap_adapter_072 import assess_ridge_cap_adapters
from brickhouse.bricks.ridge_tile_upper_interface_073 import (
    inspect_3002_26603_upper_interface,
)


def head(x=20, y=11, z=12, rotation=0):
    return BrickModelPart(
        placement_id="cap", part_id="BRICK_2X3",
        category="brick", component="roof_support",
        x_studs=x, y_studs=y, z_plates=z,
        rotation_quarter_turns=rotation,
    )


def cover(x=20, y=11, z=15, rotation=0, part_id="TILE_2X3"):
    return BrickModelPart(
        placement_id="tile", part_id=part_id,
        category="ridge_tile", component="roof", roof_side="ridge",
        x_studs=x, y_studs=y, z_plates=z,
        rotation_quarter_turns=rotation,
    )


@pytest.mark.parametrize("x,y,z,turns,axes", [
    (20, 11, 12, 0, [[21, 12], [21, 13]]),
    (15, 4, 96, 1, [[16, 5], [17, 5]]),
    (38, 13, 3, 2, [[39, 14], [39, 15]]),
    (3, 40, 36, 3, [[4, 41], [5, 41]]),
])
def test_verified_nominal_six_studs_and_two_tubes_in_two_roof_axes(
        x, y, z, turns, axes):
    cap = head(x, y, z, turns)
    tile = cover(x, y, z + 3, turns)
    report = inspect_3002_26603_upper_interface(cap, tile)
    assert report["status"] == "NOMINAL_LDRAW_STUD_AND_TUBE_LAYOUT_ONLY"
    assert report["two_underside_tube_axes_studs"] == axes
    assert len(report["six_head_stud_cells"]) == 6
    assert len(report["tube_surrounding_stud_cells"]) == 2
    assert all(len(cells) == 4 for cells in report["tube_surrounding_stud_cells"])
    assert report["tube_outer_stud_clearance_ldu"] > 0
    assert report["stud_plane_plates"] == tile.z_plates
    assert report["orthogonal_connector_gate"] == "UNKNOWN"
    assert report["upper_clutch"].startswith("UNKNOWN")
    assert report["perimeter_clutch_strength"].startswith("UNKNOWN")
    assert report["physical_certification"] == "NOT_CERTIFIED"


def test_vertical_displacement_rejected_without_false_connector_claim():
    report = inspect_3002_26603_upper_interface(head(), cover(z=16))
    assert report["status"] == "REJECTED_UNMATCHED_VERTICAL_CONNECTOR_PLANE"
    assert report["upper_clutch"].startswith("UNKNOWN")


def test_horizontal_displacement_rejected_even_if_bounding_boxes_overlap():
    report = inspect_3002_26603_upper_interface(head(), cover(x=21))
    assert report["status"] == "REJECTED_UNMATCHED_2X3_FOOTPRINT"
    assert report["upper_clutch"].startswith("UNKNOWN")


def test_unreviewed_rotation_and_tile_not_promoted_to_valid():
    assert inspect_3002_26603_upper_interface(
        head(), cover(rotation=1))["status"] == "UNKNOWN_UNREVIEWED_RELATIVE_ROTATION"
    assert inspect_3002_26603_upper_interface(
        head(), cover(part_id="TILE_2X4"))["status"] == "UNKNOWN_UNREVIEWED_PART_FAMILY"


def _slope(pid, side, x, y, z, rotation=0):
    return BrickModelPart(
        placement_id=pid, part_id="BRICK_SLOPED_18_4X2",
        category="roof_tile", component="roof", roof_side=side,
        x_studs=x, y_studs=y, z_plates=z,
        rotation_quarter_turns=rotation,
    )


def _wall(pid, x, y, z):
    return BrickModelPart(
        placement_id=pid, part_id="BRICK_1X1", category="brick",
        component="wall", facade="front",
        x_studs=x, y_studs=y, z_plates=z, rotation_quarter_turns=0,
    )


def _house(shift=0, rotation=0, anchored=True):
    if rotation == 0:
        neg, pos, anchor = ((38 + shift, 2), (39 + shift, 2), (40 + shift, 2))
        roof_z, top = 117, 111
    else:
        neg, pos, anchor = ((14 + shift, 2), (14 + shift, 2), (14 + shift, 3))
        roof_z, top = 93, 87
    parts = [
        _slope("negative", "negative", *neg, roof_z, rotation),
        _slope("positive", "positive", *pos, roof_z, rotation),
        *[_wall(f"wall-{z}", *anchor, z)
          for z in (range(0, top+1, 3) if anchored else [top])],
    ]
    return BrickModel(
        building_id=f"other-house-{shift}-{rotation}-{anchored}",
        volume_id="v", width_studs=100, depth_studs=100,
        height_plates=180, parts=parts,
    )


def test_existing_ridge_adapter_exposes_nominal_upward_mating_without_certifying():
    model = _house(shift=6)
    original = model.model_dump_json()
    result = assess_ridge_cap_adapters(model)
    site = result["sites"][0]
    assert site["upper_interface_geometry"]["status"] == "NOMINAL_LDRAW_STUD_AND_TUBE_LAYOUT_ONLY"
    assert site["upper_interface_geometry"]["orthogonal_connector_gate"] == "UNKNOWN"
    assert site["headpiece_to_ridge_tile"].startswith("UNKNOWN")
    assert site["host_support_path"] == "DOCUMENTED_NOMINAL_WALL_STUD_PATH_TO_Z0"
    assert site["lower_post_to_headpiece"] == "VALID"
    assert result["physical_certification"] == "NOT_CERTIFIED"
    assert result["model_mutated"] is False
    assert model.model_dump_json() == original


def test_unanchored_second_house_never_gets_headpiece_or_top_mating():
    m = _house(shift=12, anchored=False)
    r = assess_ridge_cap_adapters(m)
    assert r["sites"][0]["headpiece"] is None
    assert r["sites"][0]["upper_interface_geometry"]["status"] == "UNKNOWN_NOT_EVALUATED"
    assert r["physical_certification"] == "NOT_CERTIFIED"


def test_perpendicular_gable_2x4_stays_unknown_no_artificial_headpiece():
    m = _house(rotation=1)
    saved = m.model_dump_json()
    r = assess_ridge_cap_adapters(m)
    assert r["sites"][0]["status"] == "UNKNOWN_UNREVIEWED_CAP_DIMENSIONS"
    assert r["sites"][0]["upper_interface_geometry"]["status"] == "UNKNOWN_NOT_EVALUATED"
    assert m.model_dump_json() == saved


def test_ldraw_mesh_probe_remains_independent_from_stud_layout():
    m = _house()
    lib = LDrawLibrary(Path("lego_geometry_engine/tests/fixtures/ldraw"))
    r = assess_ridge_cap_adapters(m, library=lib)
    site = r["sites"][0]
    assert site["upper_interface_geometry"]["status"] == "NOMINAL_LDRAW_STUD_AND_TUBE_LAYOUT_ONLY"
    assert site["mesh_pairs_required"] >= 1
    assert r["mesh_pairs_checked"] == site["mesh_pairs_required"]
    assert site["status"] in (
        "MESH_INTERSECTION_REVIEW_REQUIRED",
        "UNKNOWN_UNREVIEWED_OR_MISSING_LDRAW_GEOMETRY",
        "HEADPIECE_MESH_SCREEN_ONLY_CLUTCH_UNKNOWN",
    )
    assert site["headpiece_to_ridge_tile"].startswith("UNKNOWN")


def test_guided004_is_unchanged_if_artifact_available():
    p = Path("artifacts/lego2-guided-004/brick-model.json")
    if not p.is_file():
        pytest.skip("canonical 1890-piece model not in checkout")
    m = BrickModel.model_validate_json(p.read_text(encoding="utf-8"))
    assert len(m.parts) == 1890
    saved = m.model_dump_json()
    r = assess_ridge_cap_adapters(m, max_sites=2)
    assert r["original_part_count"] == 1890
    assert r["model_mutated"] is False
    assert r["physical_certification"] == "NOT_CERTIFIED"
    assert m.model_dump_json() == saved
