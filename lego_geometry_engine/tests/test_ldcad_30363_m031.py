"""Mission 031 — CC BY-SA LDCad shadows loaded optionally, no copied data.

Genuine LDraw meshes + external pinned ShadowLibrary for one B3 pair ONLY.
"""
from __future__ import annotations
import os
from pathlib import Path
from shutil import copytree

import pytest
from lego_geometry_engine import (
    LDrawLibrary, Transform, Relation, analyze_assembly, find_connections,
    instance_from_dict, instantiate,
)
from lego_geometry_engine import assembly as assembly_module
from lego_geometry_engine.core import PartDefinition
from dataclasses import replace
from importlib import util

if not os.environ.get("LDRAW_ROOT") or not os.environ.get("LDCAD_SHADOW_ROOT"):
    pytest.skip("Pinned real LDraw and LDCad shadow roots required", allow_module_level=True)

LDRAW_ROOT = Path(os.environ["LDRAW_ROOT"])
SHADOW_ROOT = Path(os.environ["LDCAD_SHADOW_ROOT"])
REV = "9b1131fb1991f8c0bfc072325e4e12f6271aba35"


@pytest.fixture(scope="module")
def lib():
    return LDrawLibrary(LDRAW_ROOT, ldcad_shadow_root=SHADOW_ROOT)


@pytest.fixture(scope="module")
def model_pair(lib):
    # B3's EXACT two input LDraw placements, no edits to B3 or other parts.
    roof = instance_from_dict({
        "instance_id": "roof-000048", "part_id": "30363.dat", "color": 7,
        "transform": [470,-816,60, 0,0,1, 0,1,0, -1,0,0],
    }, lib)
    brick = instance_from_dict({
        "instance_id": "gable-000006", "part_id": "3004.dat", "color": 7,
        "transform": [480,-792,50, 1,0,0, 0,1,0, 0,0,1],
    }, lib)
    return roof, brick


def test_a_eight_lower_snap_sites_and_source_depths(lib):
    slope = lib.load_part("30363.dat")
    assert len(slope.triangles) == 700
    assert lib.ldcad_shadow_status == "EIGHT_FEMALE_SNAP_SITES_NOMINAL_ONLY"
    lower = [c for c in slope.connectors if c.type == "anti_stud"]
    top = [c for c in slope.connectors if c.type == "stud"]
    assert len(lower) == 8
    assert len(top) == 2
    assert {c.position for c in top} == {(-10.,0.,0.),(10.,0.,0.)}
    for z, depth in [(0.,20.),(-20.,14.),(-40.,8.),(-60.,4.)]:
        row = [c for c in lower if c.position[2] == z]
        assert {c.position for c in row} == {(-10.,24.,z),(10.,24.,z)}
        assert all(c.snap_depth_ldu == depth for c in row)
        assert all(c.orientation == (0,1,0) for c in row)
        assert all(c.metadata_origin and REV in c.metadata_origin for c in row)


def test_b_exact_B3_one_nominal_connection_and_flags(model_pair):
    slope, brick = model_pair
    matches = find_connections(slope, brick)
    assert len(matches) == 1, matches
    match=matches[0]
    assert match["position"] == (470.,-792.,50.)
    assert match["type"] == "anti_stud:stud"
    assert match["female_depth_ldu"] == 20.
    assert match["nominal_connection_recognized"] is True
    assert match["absence_of_collision_validated"] is False
    assert match["insertion_validated"] is False
    assert match["stability_validated"] is False
    assert not any(m["position"] == (490.,-792.,50.) for m in matches)


def test_c_wrong_translation_and_rotation_rejected(model_pair):
    slope, brick = model_pair
    wrong = instantiate(brick.definition,"wrong-x",
                        Transform.translation(490.,-792.,50.))
    assert find_connections(slope,wrong) == []
    wrong_rot = Transform((
        (1,0,0,480),
        (0,0,-1,-792),
        (0,1,0,50),
        (0,0,0,1),
    ))
    wrong_ori = instantiate(brick.definition,"wrong-axis",wrong_rot)
    assert find_connections(slope,wrong_ori) == []


def test_d_original_M026_top_studs_still_match_a_brick_above(lib):
    slope=instantiate(lib.load_part("30363.dat"), "slope")
    brick=instantiate(lib.load_part("3004.dat"), "brick-above",
                      Transform.translation(0,-24,0))
    matches = find_connections(slope,brick)
    assert len(matches) == 2
    assert all(m["type"] == "stud:anti_stud" for m in matches)


def test_e_collision_never_becomes_acceptable_with_LDCad(model_pair,monkeypatch):
    slope,brick = model_pair
    assert find_connections(slope,brick)
    monkeypatch.setattr(assembly_module,"check_collision",lambda *_: Relation.COLLISION)
    r=analyze_assembly([slope,brick])
    assert not r.valid
    assert r.collisions and r.collisions[0]["type"] == (
        "slope_30363_mesh_intersection_review_required"
    )


def test_f_without_shadow_or_with_missing_files_fail_closed(tmp_path):
    bare = LDrawLibrary(LDRAW_ROOT)
    assert len([c for c in bare.load_part("30363.dat").connectors
                if c.type=="anti_stud"]) == 0
    missing = LDrawLibrary(LDRAW_ROOT,ldcad_shadow_root=tmp_path)
    assert len([c for c in missing.load_part("30363.dat").connectors
                if c.type=="anti_stud"]) == 0
    assert len([c for c in missing.load_part("30363.dat").connectors
                if c.type=="stud"]) == 2


@pytest.mark.parametrize("substitution", [
    "[gender=M]", "[secs=R 6 99]", "[grid=C 3 1 20 0]",
    "[ori=1 1 0 0 1 0 0 0 1]", "[caps=none]",
])
def test_g_invalid_or_unknown_shadow_rejected_without_partial_connector(
    tmp_path, substitution
):
    root = tmp_path / "shadows"
    copytree(SHADOW_ROOT,root)
    f=root/"parts/s/30363s01.dat"
    s=f.read_text(encoding="utf-8")
    old = {
        "[gender=M]": "[gender=F]",
        "[secs=R 6 99]": "[secs=R 6 20]",
        "[grid=C 3 1 20 0]": "[grid=C 2 1 20 0]",
        "[ori=1 1 0 0 1 0 0 0 1]": "[pos=0 24 0]",
        "[caps=none]": "[caps=one]",
    }[substitution]
    assert old in s
    f.write_text(s.replace(old, substitution, 1), encoding="utf-8")
    u=LDrawLibrary(LDRAW_ROOT,ldcad_shadow_root=root)
    slope=u.load_part("30363.dat")
    assert not any(c.type=="anti_stud" for c in slope.connectors)
    assert len([c for c in slope.connectors if c.type=="stud"])==2
    assert u.ldcad_shadow_status.startswith("FAIL_CLOSED_")


def test_h_standard_3004_and_3005_connectors_unchanged(lib):
    assert len(lib.load_part("3004.dat").connectors) == 4
    assert len(lib.load_part("3005.dat").connectors) == 2
    assert all(c.metadata_origin is None
               for c in lib.load_part("3004.dat").connectors)


def test_i_shadow_subpart_references_and_male_inheritance(lib):
    main= (LDRAW_ROOT/"parts/30363.dat").read_text(encoding="utf-8")
    sub= (LDRAW_ROOT/"parts/s/30363s01.dat").read_text(encoding="utf-8")
    main3004=(LDRAW_ROOT/"parts/3004.dat").read_text(encoding="utf-8")
    sub3004=(LDRAW_ROOT/"parts/s/3004s01.dat").read_text(encoding="utf-8")
    assert "s\\30363s01.dat" in main
    assert "s\\3004s01.dat" in main3004
    assert sum(line.endswith("stud.dat") for line in sub3004.splitlines())==2
    assert len([c for c in lib.load_part("30363.dat").connectors
                if c.metadata_origin])==8
