from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FRONTEND=ROOT/"frontend"
WIDTHS=(24,32,51,57)
ALLOWED={f"BRICK_1X{n}" for n in (1,2,3,4,6,8,10)}

def load(width:int):
    return json.loads((FRONTEND/"experiments"/"scale-prototypes"/f"scale-{width}-front-export.json").read_text(encoding="utf-8"))

def footprint(part):
    length=int(part["part_id"].split("X")[-1])
    return part["x_studs"],part["x_studs"]+length,part["z_plates"]//3,part["z_plates"]//3+1

def test_scale_prototypes_are_comparable_and_valid():
    sources=set()
    for width in WIDTHS:
        b=load(width); m=b["brick_model"]; meta=b["metadata"]
        assert meta["experiment_kind"]=="EXPERIMENTAL_SCALE_PROTOTYPE"
        assert m["width_studs"]==width and m["depth_studs"]==1
        expected=round((0.83*width*8.0/3.2)/3)*3
        assert m["height_plates"]==expected
        assert b["bom"]["total_parts"]==len(m["parts"])
        assert {p["part_id"] for p in m["parts"]}<=ALLOWED
        assert all(p["y_studs"]==0 and p["z_plates"]%3==0 for p in m["parts"])
        sources.add(meta["source_model"])
        cells=set()
        for p in m["parts"]:
            x0,x1,z0,z1=footprint(p)
            assert 0<=x0<x1<=width and 0<=z0<z1<=m["height_plates"]//3
            for cell in ((x,z) for x in range(x0,x1) for z in range(z0,z1)):
                assert cell not in cells
                cells.add(cell)
        openings=meta["architectural_openings"]
        assert [o["family"] for o in openings].count("repeated-large")==4\n        f1=[o for o in openings if o["family"]=="repeated-large"]\n        assert len({(o["x1"]-o["x0"],o["z1_course"]-o["z0_course"]) for o in f1})==1\n        template=meta["f1_family_template"]\n        assert {(o["x1"]-o["x0"],o["z1_course"]-o["z0_course"]) for o in f1}=={(template["width_studs"],template["height_brick_courses"])}
        for o in openings:
            for x in range(o["x0"],o["x1"]):
                for z in range(o["z0_course"],o["z1_course"]):
                    assert (x,z) not in cells
    assert sources=={"BOLDUNGO-CONSTRUCTIVE-SCALE-DISCRIMINANTS-010"}

def test_precision_uses_rendered_bundle_before_local_storage():
    viewer=(FRONTEND/"viewer.js").read_text(encoding="utf-8")
    precision=(FRONTEND/"viewer-precision.js").read_text(encoding="utf-8")
    assert "window.__BRICKHOUSE_CURRENT_BUNDLE__=b" in viewer
    assert "if(window.__BRICKHOUSE_CURRENT_BUNDLE__)return window.__BRICKHOUSE_CURRENT_BUNDLE__" in precision

def test_comparison_page_exposes_all_four_widths():
    page=(FRONTEND/"scale-prototypes.html").read_text(encoding="utf-8")
    for width in WIDTHS:
        assert f'data-w="{width}"' in page
    assert "viewer.html?bundle=" in page
