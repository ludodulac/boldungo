"""LEGO2-077: simultaneous four-piece ridge geometry and insertion evidence."""
from pathlib import Path

import pytest
from lego_geometry_engine import LDrawLibrary

from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.ridge_four_piece_assembly_077 import (
    review_simultaneous_ridge_assembly,
)


def roof(pid, side, x, y, z, rotation=0, part_id="BRICK_SLOPED_18_4X2"):
    return BrickModelPart(
        placement_id=pid, part_id=part_id, category="roof_tile",
        component="roof", roof_side=side, x_studs=x, y_studs=y,
        z_plates=z, rotation_quarter_turns=rotation,
    )


def wall(pid, x, y, z):
    return BrickModelPart(
        placement_id=pid, part_id="BRICK_1X1", category="brick",
        component="wall", facade="front", x_studs=x, y_studs=y,
        z_plates=z, rotation_quarter_turns=0,
    )


def house(*parts):
    return BrickModel(
        building_id="four-piece-fixture", volume_id="v",
        width_studs=120, depth_studs=120, height_plates=180,
        parts=list(parts),
    )


def anchored(x, y, top):
    return [wall(f"wall-{x}-{y}-{z}", x, y, z)
            for z in range(0, top + 1, 3)]


def gable(*, rotation=0, shift=0, floating=False):
    if rotation == 0:
        coords = ((38 + shift, 0), (39 + shift, 0))
        x, y, z, host_z = (40 + shift, 0, 117, 111)
    else:
        coords = ((14 + shift, 2), (14 + shift, 2))
        x, y, z, host_z = (14 + shift, 3, 93, 87)
    posts = ([wall("floating", x, y, host_z)] if floating
             else anchored(x, y, host_z))
    return house(
        roof("neg", "negative", *coords[0], z, rotation),
        roof("pos", "positive", *coords[1], z, rotation),
        *posts,
    )


@pytest.mark.parametrize("rotation,shift,part,plane", [
    (0, 0, "TILE_2X3", 120),
    (0, 11, "TILE_2X3", 120),
    (1, 0, "TILE_2X4", 96),
    (1, 9, "TILE_2X4", 96),
])
def test_exact_virtual_four_piece_positions_no_model_mutation(rotation, shift, part, plane):
    model = gable(rotation=rotation, shift=shift)
    snapshot = model.model_dump_json()
    r = review_simultaneous_ridge_assembly(model)
    assert r["sites_checked"] == 1
    row = r["sites"][0]
    assert row["component_count"] == 4
    assert [p["role"] for p in row["components"]] == [
        "central_post", "ridge_cover", "negative_slope", "positive_slope"]
    assert row["components"][1]["part_id"] == part
    assert row["components"][1]["z_plates"] == plane
    assert row["components"][2]["z_plates"] == plane - 3
    assert row["components"][3]["z_plates"] == plane - 3
    assert row["central_stud_collision"] == "NO_DUPLICATED_DOCUMENTED_TOP_STUD_CELLS"
    assert row["host_anchor_status"] == "DOCUMENTED_NOMINAL_WALL_STUD_PATH_TO_Z0"
    assert row["nominal_wall_post_connectors"] == ["VALID", "VALID"]
    assert row["status"] == "UNKNOWN"
    assert row["reason"] == "LDRAW_LIBRARY_REQUIRED_FOR_SIMULTANEOUS_MESH"
    assert row["post_to_cover_clutch"].startswith("UNKNOWN")
    assert row["negative_slope_to_cover_clutch"].startswith("UNKNOWN")
    assert row["positive_slope_to_cover_clutch"].startswith("UNKNOWN")
    assert row["post_stack_insertion"].startswith("UNKNOWN")
    assert row["slope_installation"].startswith("UNKNOWN")
    assert r["physical_certification"] == "NOT_CERTIFIED"
    assert r["model_mutated"] is False
    assert model.model_dump_json() == snapshot


def test_simultaneous_mesh_six_pairs_plus_covered_insertion_path(monkeypatch):
    call_log = []
    def separated(a, b, library, cache, relation_cache):
        call_log.append((a.placement_id, b.placement_id, a.z_plates))
        return {"part_a": a.placement_id, "part_b": b.placement_id,
                "status": "MESH_SEPARATED", "mesh_relation": "SEPARATED"}
    monkeypatch.setattr("brickhouse.bricks.ridge_four_piece_assembly_077._pair", separated)
    m = gable()
    before = m.model_dump_json()
    r = review_simultaneous_ridge_assembly(m, library=object())
    row = r["sites"][0]
    assert row["component_count"] == 4
    assert len(row["simultaneous_pair_checks"]) == 6
    assert r["mesh_pairs_computed"] == 15  # 6 seated + 9 elevated
    assert [s["lift_plates"] for s in row["cover_insertion_samples"]] == [3, 2, 1, 0]
    assert all(len(s["checks"]) == 3 for s in row["cover_insertion_samples"])
    assert not row["missing_pair_checks"]
    assert not any(s["unchecked"] for s in row["cover_insertion_samples"])
    assert row["status"] == "UNKNOWN"
    assert row["reason"] == "DISCRETE_MESH_SCREEN_ONLY_NO_MECHANICAL_CLUTCH_PROOF"
    assert row["cover_insertion"] == "UNKNOWN_CONTINUOUS_PATH_UNPROVEN"
    assert row["load_and_stiffness"] == "UNKNOWN_NOT_MEASURED"
    assert row["physical_certification"] == "NOT_CERTIFIED"
    assert m.model_dump_json() == before


def test_collision_of_two_roof_slopes_is_review_not_valid(monkeypatch):
    def mesh(a, b, library, cache, relation_cache):
        collided = {a.roof_side, b.roof_side} == {"negative", "positive"}
        return {"part_a": a.placement_id, "part_b": b.placement_id,
                "status": ("MESH_INTERSECTION_REVIEW_REQUIRED" if collided
                           else "MESH_CONTACT_REVIEW_REQUIRED"),
                "mesh_relation": "COLLISION" if collided else "CONTACT"}
    monkeypatch.setattr("brickhouse.bricks.ridge_four_piece_assembly_077._pair", mesh)
    r = review_simultaneous_ridge_assembly(gable(), library=object())
    row = r["sites"][0]
    assert row["status"] == "REVIEW_REQUIRED"
    assert row["reason"] == "FOUR_PART_MESH_INTERSECTION_NEEDS_CONNECTOR_AWARE_REVIEW"
    assert r["physical_certification"] == "NOT_CERTIFIED"


def test_pairwise_complete_checks_still_cannot_prove_triple_clutch(monkeypatch):
    def contact(a, b, library, cache, relation_cache):
        return {"part_a": a.placement_id, "part_b": b.placement_id,
                "status": "MESH_CONTACT_REVIEW_REQUIRED", "mesh_relation": "CONTACT"}
    monkeypatch.setattr("brickhouse.bricks.ridge_four_piece_assembly_077._pair", contact)
    r = review_simultaneous_ridge_assembly(gable(shift=4), library=object())
    assert len(r["sites"][0]["simultaneous_pair_checks"]) == 6
    assert r["sites"][0]["status"] == "UNKNOWN"
    assert r["physical_certification"] == "NOT_CERTIFIED"


def test_fixture_ldraw_missing_26603_and_30363_remains_unknown():
    library = LDrawLibrary(Path("lego_geometry_engine/tests/fixtures/ldraw"))
    m = gable()
    before = m.model_dump_json()
    r = review_simultaneous_ridge_assembly(m, library=library)
    row = r["sites"][0]
    assert row["component_count"] == 4
    assert len(row["simultaneous_pair_checks"]) == 6
    assert r["mesh_pairs_computed"] == 15
    assert row["status"] == "UNKNOWN"
    assert row["reason"] == "UNAVAILABLE_COMPLETE_OFFICIAL_LDRAW_GEOMETRY"
    assert all(c["status"] == "UNKNOWN_GEOMETRY_UNAVAILABLE"
               for c in row["simultaneous_pair_checks"])
    assert m.model_dump_json() == before


def test_incomplete_budget_reports_every_omitted_pair_and_path_step(monkeypatch):
    def separate(a, b, library, cache, relation_cache):
        return {"part_a": a.placement_id, "part_b": b.placement_id,
                "status": "MESH_SEPARATED", "mesh_relation": "SEPARATED"}
    monkeypatch.setattr("brickhouse.bricks.ridge_four_piece_assembly_077._pair", separate)
    r = review_simultaneous_ridge_assembly(gable(), library=object(), max_mesh_pairs=3)
    row = r["sites"][0]
    assert row["component_count"] == 4
    assert len(row["simultaneous_pair_checks"]) == 3
    assert len(row["missing_pair_checks"]) == 3
    assert row["reason"] == "INCOMPLETE_SIMULTANEOUS_OR_INSERTION_MESH_BUDGET"
    assert row["status"] == "UNKNOWN"
    assert r["mesh_pairs_computed"] == 3


def test_unanchored_central_post_does_not_pass_as_supported():
    r = review_simultaneous_ridge_assembly(gable(floating=True))
    row = r["sites"][0]
    assert row["component_count"] == 0
    assert row["host_anchor_status"] == "UNKNOWN_NO_DOCUMENTED_WALL_LOAD_PATH"
    assert row["status"] == "UNKNOWN"
    assert row["reason"] == "NO_FOUR_PART_CONFIGURATION_WITH_DOCUMENTED_ANCHOR"


def test_monopitch_and_single_slope_have_no_fake_four_piece_ridge():
    mono = house(roof("mono", "slope", 5, 5, 9,
                      part_id="BRICK_SLOPED_45_2X4"))
    single = house(roof("half", "negative", 38, 0, 117),
                   *anchored(40, 0, 111))
    for m in (mono, single):
        r = review_simultaneous_ridge_assembly(m)
        assert r["sites_checked"] == 0
        assert r["mesh_pairs_computed"] == 0
        assert r["physical_certification"] == "NOT_CERTIFIED"


@pytest.mark.parametrize("lifts", [
    (), (3, 2, 1), (0, 2), (3, 3, 0), (-1, 0), (2.5, 0),
    tuple(range(12, -1, -1)),
])
def test_invalid_insertion_sample_plan_is_rejected(lifts):
    with pytest.raises(ValueError):
        review_simultaneous_ridge_assembly(gable(), cover_lift_plates=lifts)


def test_max_budget_must_be_positive():
    for opts in ({"max_sites": 0}, {"max_mesh_pairs": 0}):
        with pytest.raises(ValueError):
            review_simultaneous_ridge_assembly(gable(), **opts)


def test_guided004_exact_1890_parts_unchanged():
    p = Path("artifacts/lego2-guided-004/brick-model.json")
    if not p.is_file():
        pytest.skip("canonical model not available in checkout")
    model = BrickModel.model_validate_json(p.read_text(encoding="utf-8"))
    assert len(model.parts) == 1890
    before = model.model_dump_json()
    report = review_simultaneous_ridge_assembly(model, max_sites=2)
    assert report["original_part_count"] == 1890
    assert report["model_mutated"] is False
    assert report["physical_certification"] == "NOT_CERTIFIED"
    assert model.model_dump_json() == before
