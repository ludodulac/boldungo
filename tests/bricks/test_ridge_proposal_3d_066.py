"""066: bounded prototype tests; no fake proof from incomplete geometry."""
from pathlib import Path
from types import SimpleNamespace

import pytest
from lego_geometry_engine import LDrawLibrary

from brickhouse.bricks.ridge_proposal_3d_066 import probe_proposed_ridges

FIXTURE = Path("lego_geometry_engine/tests/fixtures/ldraw")


def slope(pid, side, x, y, z):
    return SimpleNamespace(
        placement_id=pid, component="roof", category="roof_tile",
        part_id="BRICK_SLOPED_18_4X2", roof_side=side,
        x_studs=x, y_studs=y, z_plates=z, rotation_quarter_turns=0,
    )


def ridge(pid, x, y, z):
    return SimpleNamespace(
        placement_id=pid, component="roof", category="ridge_tile",
        part_id="TILE_2X4", roof_side="ridge",
        x_studs=x, y_studs=y, z_plates=z, rotation_quarter_turns=0,
    )


def house():
    return SimpleNamespace(
        building_id="different-house",
        parts=[
            slope("neg", "negative", 38, 0, 117),
            slope("pos", "positive", 39, 0, 117),
            ridge("old", 39, 0, 120),
        ],
    )


def test_missing_full_ldraw_must_be_unknown_not_collision_free():
    model = house()
    before = [(p.placement_id, p.part_id, p.z_plates) for p in model.parts]
    report = probe_proposed_ridges(model, LDrawLibrary(FIXTURE))
    assert report["proposed_total"] == 1
    assert report["proposals_checked"] == 1
    sample = report["sample"][0]
    assert sample["tile"]["part_id"] == "TILE_2X3"
    assert sample["supporting_slope_ids"] == {
        "negative": ["neg"], "positive": ["pos"]
    }
    assert len(sample["tile_to_slopes"]) == 2
    assert len(sample["opposing_slopes"]) == 1
    assert all(x["status"] == "UNKNOWN_GEOMETRY_UNAVAILABLE"
               for x in sample["tile_to_slopes"] + sample["opposing_slopes"])
    assert sample["underside_clutch"] == "UNKNOWN"
    assert report["physical_certification"] == "NOT_CERTIFIED"
    assert report["model_mutated"] is False
    assert before == [(p.placement_id, p.part_id, p.z_plates) for p in model.parts]


def test_bounds_and_empty_roof_not_implicitly_certified():
    model = house()
    with pytest.raises(ValueError, match="max_tiles"):
        probe_proposed_ridges(model, LDrawLibrary(FIXTURE), max_tiles=0)
    model.parts = [ridge("alone", 39, 0, 120)]
    result = probe_proposed_ridges(model, LDrawLibrary(FIXTURE))
    assert result["proposed_total"] == 0
    assert result["proposals_checked"] == 0
    assert result["physical_certification"] == "NOT_CERTIFIED"


def test_mirror_paths_allow_only_normalized_ldraw_entries():
    from scripts.download_ldraw_probe_066 import locations, TYPE1

    assert locations(r"s\30363s01.dat") == ["parts/s/30363s01.dat"]
    assert locations("stud.dat") == ["parts/stud.dat", "p/stud.dat"]
    assert locations("48/1-4edge.dat") == ["p/48/1-4edge.dat"]
    with pytest.raises(ValueError):
        locations("../invalid.dat")
    assert TYPE1.match("1 16 0 0 0 1 0 0 0 1 0 0 0 1 s\\30363s01.dat")
