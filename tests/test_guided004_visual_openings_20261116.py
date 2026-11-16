"""Regression guards for the limited GUIDED004 browser-visual corrections.

The 2853-volume browser export remains a NON-CERTIFIED visual approximation.
These checks do not certify LDraw assembly or mechanical fit.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "frontend/data/boldungo2-lego-house-019.json"


def load():
    b = json.loads(SOURCE.read_text(encoding="utf-8"))
    return b, {p["placement_id"]: p for p in b["brick_model"]["parts"]}


def test_glass_bricks_are_a_regular_six_by_five_stud_grid():
    b, _ = load()
    glass = [p for p in b["brick_model"]["parts"] if p.get("opening_id") == "right_glass_blocks"]
    assert len(glass) == 30
    assert {p["ldraw_part_id"] for p in glass} == {"3005.dat"}
    assert {p["part_id"] for p in glass} == {"BRICK_1X1"}
    assert {p["component"] for p in glass} == {"glass_block"}
    assert {p["length_studs"] for p in glass} == {1}
    assert {p["height_plates"] for p in glass} == {3}
    assert sorted({p["y_studs"] for p in glass}) == [23, 24, 25, 26, 27, 28]
    assert sorted({p["z_plates"] for p in glass}) == [8, 11, 14, 17, 20]
    assert len({(p["y_studs"], p["z_plates"]) for p in glass}) == 30


def test_front_glazed_door_has_no_header_gap_in_visual_grid():
    _, parts = load()
    left, right = parts["b2-005-0946"], parts["b2-005-0947"]
    upper, extra = parts["b2-005-0945"], parts["guided004-visual-fix-front-glazed-door-top-1x2"]
    assert left["height_plates"] == right["height_plates"] == 24
    assert (upper["x_studs"], upper["width_studs"], upper["z_plates"], upper["height_plates"]) == (45, 8, 24, 3)
    assert (extra["x_studs"], extra["width_studs"], extra["z_plates"], extra["height_plates"]) == (53, 2, 24, 3)
    assert (upper["ldraw_part_id"], extra["ldraw_part_id"]) == ("3008.dat", "3004.dat")
    assert upper["z_plates"] + upper["height_plates"] == 27


def test_terrace_side_panels_recentered_and_correctly_oriented():
    _, parts = load()
    assert parts["b2-005-0998"]["x_studs"] == 15.88
    assert parts["b2-005-1003"]["x_studs"] == 15.88
    source = (ROOT / "frontend/viewer.js").read_text(encoding="utf-8")
    assert "geo=w>=l?new THREE.BoxGeometry(w*.98,h,thickness):new THREE.BoxGeometry(thickness,h,l*.98)" in source
    assert "p.component!=='glass_block'" in source


def test_export_bom_still_matches_all_parts():
    b, _ = load()
    parts = b["brick_model"]["parts"]
    assert len(parts) == b["bom"]["total_parts"] == 2853
    assert len({p["placement_id"] for p in parts}) == len(parts)
    assert b["bom"]["unique_part_types"] == len({p["part_id"] for p in parts})
    by_type = {}
    for p in parts:
        key = (p["part_id"], p["category"])
        by_type[key] = by_type.get(key, 0) + 1
    assert by_type == {(x["part_id"], x["category"]): x["quantity"] for x in b["bom"]["lines"]}
