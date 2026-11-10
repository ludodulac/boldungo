"""M026: source-proven 30363 upper studs; underside stays unknown.

All physical examples use genuine pinned LDraw 30363 and 3004 meshes.
Synthetic collision in one policy test only stubs the collision RESULT,
not geometries or connector coordinates, to guard against collision masking.
"""
import os
from pathlib import Path

import pytest

from lego_geometry_engine import (
    LDrawLibrary, Relation, Transform, analyze_assembly,
    check_collision, find_connections, instantiate,
)
from lego_geometry_engine import assembly as assembly_module

if not os.environ.get("LDRAW_ROOT"):
    pytest.skip("LDRAW_ROOT must point at genuine pinned LDraw files",
                allow_module_level=True)


@pytest.fixture(scope="module")
def lib():
    return LDrawLibrary(Path(os.environ["LDRAW_ROOT"]))


@pytest.fixture(scope="module")
def pair(lib):
    slope = instantiate(lib.load_part("30363.dat"), "real-30363")
    # 3004 bottom anti-stud plane is at y=24 locally; translating it -24
    # aligns it with the two genuine slope top studs at local y=0.
    brick = instantiate(lib.load_part("3004.dat"), "real-3004",
                        Transform.translation(0, -24, 0))
    return slope, brick


def test_a_source_proven_studs_match_a_real_3004_bottom(pair):
    slope, support = pair
    assert len(slope.definition.triangles) == 700
    assert {c.position for c in slope.definition.connectors} == {
        (-10., 0., 0.), (10., 0., 0.),
    }
    assert all(c.type == "stud" for c in slope.definition.connectors)
    assert not any(c.type == "anti_stud" for c in slope.definition.connectors)
    matches = find_connections(slope, support)
    assert len(matches) == 2
    assert {tuple(c["position"]) for c in matches} == {
        (-10., 0., 0.), (10., 0., 0.),
    }
    # Proven local stud alignment != certified entire-body physical fit.


def test_b_shifted_real_brick_does_not_match_slope_studs(pair):
    slope, _ = pair
    wrong = instantiate(slope_definition_3004(pair), "wrong-placement",
                        Transform.translation(10, -24, 0))
    assert find_connections(slope, wrong) == []


def slope_definition_3004(pair):
    return pair[1].definition


def test_c_mesh_collision_even_with_matching_studs_stays_rejected(pair, monkeypatch):
    slope, support = pair
    assert len(find_connections(slope, support)) == 2
    # Unit-test the exact risk: if the existing engine reports a mesh
    # COLLISION for a connector-aligned 30363, NEVER auto-approve it.
    monkeypatch.setattr(assembly_module, "check_collision",
                        lambda *_: Relation.COLLISION)
    result = analyze_assembly([slope, support])
    assert result.valid is False
    assert len(result.collisions) == 1
    assert result.collisions[0]["type"] == (
        "slope_30363_mesh_intersection_review_required"
    )


def test_d_other_parts_keep_their_existing_connector_behavior(lib):
    brick_3004 = lib.load_part("3004.dat")
    brick_3005 = lib.load_part("3005.dat")
    assert len(brick_3004.connectors) == 4
    assert len(brick_3005.connectors) == 2
    assert len([x for x in brick_3004.connectors if x.type == "stud"]) == 2
    assert len([x for x in brick_3004.connectors if x.type == "anti_stud"]) == 2
    assert brick_3004 is lib.load_part("3004.dat")
    assert lib.load_part("30363.dat") is lib.load_part("30363.dat")


def test_e_no_connectors_inferred_from_name_or_bounding_box_alone(tmp_path):
    part = tmp_path / "parts"
    part.mkdir()
    (part / "30363.dat").write_text(
        "0 Slope Brick 18  4 x  2\n"
        "3 16 0 0 0 20 0 0 0 24 20\n",
        encoding="utf-8",
    )
    fake_lib = LDrawLibrary(tmp_path)
    definition = fake_lib.load_part("30363.dat")
    assert not definition.connectors
