"""078: bounded real-LDraw runner; unit tests never download third-party data."""
from pathlib import Path

import pytest

from brickhouse.bricks.brick_model import BrickModelPart
from scripts.probe_ridge_full_ldraw_078 import (
    REQUIRED_PARTS, REAL_MESH_RELATIONS, run_probe, small_ridge_model,
)


@pytest.mark.parametrize("rotation,cover_part,top", [
    (0, "TILE_2X3", 120),
    (1, "TILE_2X4", 96),
])
def test_reference_models_use_two_original_slope_positions(rotation, cover_part, top):
    model = small_ridge_model(rotation, shift=5)
    before = model.model_dump_json()
    slopes = [p for p in model.parts if p.component == "roof"]
    assert len(slopes) == 2
    assert {p.roof_side for p in slopes} == {"negative", "positive"}
    assert all(p.part_id == "BRICK_SLOPED_18_4X2" for p in slopes)
    assert all(p.z_plates == top - 3 for p in slopes)
    assert any(p.component == "wall" and p.z_plates == 0 for p in model.parts)
    assert len({p.placement_id for p in model.parts}) == len(model.parts)
    assert model.model_dump_json() == before


def test_required_real_identifiers_are_exact_not_invented():
    assert REQUIRED_PARTS == ("3005", "26603", "30363", "87079")
    assert REAL_MESH_RELATIONS == {"SEPARATED", "CONTACT", "COLLISION"}


def test_empty_library_never_passes_or_misreports_clutch(tmp_path):
    report = run_probe(tmp_path)
    assert report["complete_real_mesh_check"] is False
    assert len(report["blocking_reasons"]) >= 4
    assert set(report["required_parts"]) == set(REQUIRED_PARTS)
    assert all(not part["loadable"] for part in report["required_parts"].values())
    assert len(report["orientations"]) == 2
    for row in report["orientations"]:
        assert row["site_count"] == 1
        assert not row["six_mesh_pairs_complete"]
        assert not row["insertion_mesh_pairs_complete"]
        assert row["evidence"]["physical_certification"] == "NOT_CERTIFIED"
        assert row["evidence"]["model_mutated"] is False
    assert report["physical_certification"] == "NOT_CERTIFIED"
    assert report["model_mutated"] is False


def test_fallback_fixture_with_one_brick_cannot_claim_four_part_mesh():
    root = Path("lego_geometry_engine/tests/fixtures/ldraw")
    assert (root / "parts" / "3005.dat").is_file()
    report = run_probe(root)
    assert report["complete_real_mesh_check"] is False
    assert report["required_parts"]["3005"]["loadable"]
    for part in ("26603", "30363", "87079"):
        assert report["required_parts"][part]["loadable"] is False
    assert all(row["six_mesh_pairs_complete"] is False
               for row in report["orientations"])


def test_rotation_not_previously_reviewed_does_not_silently_fallback():
    with pytest.raises(ValueError):
        small_ridge_model(2)
