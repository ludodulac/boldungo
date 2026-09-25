from __future__ import annotations
import json
from pathlib import Path

from brickhouse.bricks.brick_model import BrickModel
from brickhouse.bricks.orthogonal_geometry import orthogonal_collisions
from brickhouse.bricks.piece_capabilities import (
    create_current_engine_capability_registry,
    validate_model_part_capabilities,
)

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
WIDTHS = (24, 32, 51, 57)
EXPECTED_F1 = {
    24: (4, 13, 1.300000),
    32: (5, 16, 1.280000),
    51: (8, 25, 1.250000),
    57: (9, 28, 1.244444),
}
EVIDENCE = "docs/evidence/f1-p1-physical-aspect-ratio-014.json"

def load(width: int):
    return json.loads((FRONTEND / "experiments" / "scale-prototypes" / f"scale-{width}-front-export.json").read_text(encoding="utf-8"))

def bounds(part):
    length = int(part["part_id"].split("X")[-1])
    if part["rotation_quarter_turns"] % 2:
        xw = length
    else:
        xw = 1
    hp = part.get("height_plates", 3 if part["category"] == "brick" else 1)
    return part["x_studs"], part["x_studs"] + xw, part["z_plates"], part["z_plates"] + hp

def test_scale_prototypes_preserve_exact_f1_physical_voids():
    registry = create_current_engine_capability_registry()
    sources = set()
    for width in WIDTHS:
        b = load(width)
        m = b["brick_model"]
        meta = b["metadata"]
        expected_width, expected_height, expected_ratio = EXPECTED_F1[width]
        assert meta["experiment_kind"] == "EXPERIMENTAL_SCALE_PROTOTYPE"
        assert meta["source_evidence"] == EVIDENCE
        assert m["width_studs"] == width and m["depth_studs"] == 1
        assert m["height_plates"] == round((0.83 * width * 8.0 / 3.2) / 3) * 3
        sources.add(meta["source_model"])

        f1 = [o for o in meta["architectural_openings"] if o["family"] == "repeated-large"]
        assert len(f1) == 4
        assert {(o["x1"] - o["x0"], o["z1_plates"] - o["z0_plates"]) for o in f1} == {(expected_width, expected_height)}
        template = meta["f1_family_template"]
        assert (template["width_studs"], template["height_plates"]) == (expected_width, expected_height)
        ratio = (expected_height * 3.2) / (expected_width * 8.0)
        assert abs(ratio - expected_ratio) < 1e-6
        assert 1.10 <= ratio <= 1.40

        occupied = set()
        for p in m["parts"]:
            x0, x1, z0, z1 = bounds(p)
            assert 0 <= x0 < x1 <= width
            assert 0 <= z0 < z1 <= m["height_plates"]
            for cell in ((x, z) for x in range(x0, x1) for z in range(z0, z1)):
                assert cell not in occupied
                occupied.add(cell)
        for o in meta["architectural_openings"]:
            for x in range(o["x0"], o["x1"]):
                for z in range(o["z0_plates"], o["z1_plates"]):
                    assert (x, z) not in occupied

        model = BrickModel.model_validate(m)
        assert orthogonal_collisions(model) == []
        validate_model_part_capabilities(model, registry)
        assert b["bom"]["total_parts"] == len(m["parts"])
        assert sum(line["quantity"] for line in b["bom"]["lines"]) == len(m["parts"])
        assert {p["part_id"] for p in m["parts"]} <= registry.approved_ids()
        assert any(p["category"] == "brick" for p in m["parts"])
        assert any(p["category"] == "plate" for p in m["parts"])
        assert json.loads(model.model_dump_json())["height_plates"] == m["height_plates"]
    assert sources == {"BOLDUNGO-CONSTRUCTIVE-SCALE-DISCRIMINANTS-010"}

def test_non_f1_opening_bounds_remain_from_012():
    expected = {
        24: {"lower-small": (6, 8, 3, 9), "lower-large": (15, 21, 0, 15)},
        32: {"lower-small": (8, 11, 6, 12), "lower-large": (21, 29, 0, 18)},
        51: {"lower-small": (12, 16, 9, 21), "lower-large": (33, 46, 3, 30)},
        57: {"lower-small": (13, 18, 12, 24), "lower-large": (37, 51, 3, 33)},
    }
    for width in WIDTHS:
        openings = {o["id"]: o for o in load(width)["metadata"]["architectural_openings"]}
        for oid, bounds_expected in expected[width].items():
            o = openings[oid]
            assert (o["x0"], o["x1"], o["z0_plates"], o["z1_plates"]) == bounds_expected

def test_precision_uses_rendered_bundle_before_local_storage():
    viewer = (FRONTEND / "viewer.js").read_text(encoding="utf-8")
    precision = (FRONTEND / "viewer-precision.js").read_text(encoding="utf-8")
    assert "window.__BRICKHOUSE_CURRENT_BUNDLE__=b" in viewer
    assert "if(window.__BRICKHOUSE_CURRENT_BUNDLE__)return window.__BRICKHOUSE_CURRENT_BUNDLE__" in precision

def test_comparison_page_exposes_all_four_widths():
    page = (FRONTEND / "scale-prototypes.html").read_text(encoding="utf-8")
    for width in WIDTHS:
        assert f'data-w="{width}"' in page
    assert "viewer.html?bundle=" in page
