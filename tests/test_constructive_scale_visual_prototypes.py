from __future__ import annotations
import json, math
from pathlib import Path
from brickhouse.bricks.brick_model import BrickModel
from brickhouse.bricks.orthogonal_geometry import orthogonal_collisions
from brickhouse.bricks.piece_capabilities import create_current_engine_capability_registry, validate_model_part_capabilities
from brickhouse.bricks.support_chain import analyze_standard_brick_support_chain

ROOT=Path(__file__).resolve().parents[1]
FRONTEND=ROOT/"frontend"
MODEL_PATH=ROOT/"docs"/"evidence"/"p1-controlled-facade-model-033.json"
WIDTHS=(24,32,51,57)

def load(w):
    return json.loads((FRONTEND/"experiments"/"scale-prototypes"/f"scale-{w}-front-export.json").read_text(encoding="utf-8"))

def bounds(p):
    length=int(p["part_id"].split("X")[-1])
    xw=length if p["rotation_quarter_turns"]%2 else 1
    hp=p.get("height_plates",1 if p["category"]=="plate" else 3)
    return p["x_studs"],p["x_studs"]+xw,p["z_plates"],p["z_plates"]+hp

def half_up(v):
    return math.floor(v+0.5)

def test_controlled_scale_prototypes_share_one_p1_model_and_only_width_varies():
    shared=json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    assert shared["experimental_variable"]=={"name":"FRONT_WIDTH_STUDS","values":[24,32,51,57]}
    fingerprints=set()
    for w in WIDTHS:
        b=load(w); m=b["metadata"]
        assert m["experiment_kind"]=="CONTROLLED_SCALE_PROTOTYPE"
        assert m["shared_normalized_model"]=="docs/evidence/p1-controlled-facade-model-033.json"
        assert m["experimental_variable"]=="FRONT_WIDTH_STUDS"
        assert m["front_width_studs"]==w
        fingerprints.add(tuple(m["source_evidence"]))
    assert len(fingerprints)==1

def test_controlled_geometry_quantization_voids_gable_support_and_exports():
    shared=json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    d=shared["derived"]; interp=shared["interpolated"]; registry=create_current_engine_capability_registry()
    for w in WIDTHS:
        b=load(w); bm=b["brick_model"]; meta=b["metadata"]; scale=2.5*w
        assert bm["width_studs"]==w and bm["depth_studs"]==1
        f1=[o for o in meta["architectural_openings"] if o["family"]=="repeated-large"]
        assert len(f1)==4
        expected_w=half_up(d["f1_family_width_norm"]*w)
        expected_h=half_up(d["f1_family_height_norm"]*scale)
        assert {(o["x1"]-o["x0"],o["z1_plates"]-o["z0_plates"]) for o in f1}=={(expected_w,expected_h)}
        occupied=set()
        for p in bm["parts"]:
            x0,x1,z0,z1=bounds(p)
            assert 0<=x0<x1<=w and 0<=z0<z1<=bm["height_plates"]
            for x in range(x0,x1):
                for z in range(z0,z1):
                    assert (x,z) not in occupied
                    occupied.add((x,z))
                    xn=(x+0.5)/w
                    seg=interp["gable_left"] if xn<=shared["observed"]["apex"][0] else interp["gable_right"]
                    edge_y=seg["m"]*xn+seg["b"]
                    cell_y=1-(z+0.5)/scale
                    assert cell_y>=edge_y-1e-12
        for o in meta["architectural_openings"]:
            for x in range(o["x0"],o["x1"]):
                for z in range(o["z0_plates"],o["z1_plates"]):
                    assert (x,z) not in occupied
        model=BrickModel.model_validate(bm)
        assert orthogonal_collisions(model)==[]
        validate_model_part_capabilities(model,registry)
        report=analyze_standard_brick_support_chain(model)
        assert report.valid and report.unsupported_placement_ids==[]
        assert b["bom"]["total_parts"]==len(bm["parts"])
        assert sum(line["quantity"] for line in b["bom"]["lines"])==len(bm["parts"])
        assert {p["part_id"] for p in bm["parts"]}<=registry.approved_ids()

def test_solid_band_metrics_are_reproducible_and_not_manually_tuned():
    shared=json.loads(MODEL_PATH.read_text(encoding="utf-8")); d=shared["derived"]
    for w in WIDTHS:
        b=load(w); meta=b["metadata"]; hp=meta["f1_family_template"]["height_plates"]
        openings={o["id"]:o for o in meta["architectural_openings"]}
        for side in ("left","right"):
            upper=openings[f"upper-{side}"]; middle=openings[f"middle-{side}"]
            gap=upper["z0_plates"]-middle["z1_plates"]
            realized=meta["realized_solid_bands"][side]
            assert realized["gap_interlevel_plates"]==gap
            assert math.isclose(realized["gap_interlevel_over_h"],gap/hp)
            assert math.isclose(meta["metrics"]["gap_interlevel_error_ratio"][side],gap/hp-d["interlevel_over_h"][side])
            assert math.isclose(meta["metrics"]["gap_top_error_ratio"][side],realized["gap_top_over_h"]-d["top_clearance_over_h"][side])
        assert meta["metrics"]["solid_band_collapse"] is False
        assert meta["metrics"]["constraint_conflicts"]==[]

def test_lower_openings_are_one_shared_p1_projection():
    shared=json.loads(MODEL_PATH.read_text(encoding="utf-8")); low=shared["observed"]["lower_openings"]
    for w in WIDTHS:
        scale=2.5*w; openings={o["id"]:o for o in load(w)["metadata"]["architectural_openings"]}
        for key,oid in (("small","lower-small"),("large","lower-large")):
            src=low[key]; o=openings[oid]
            assert (o["x0"],o["x1"],o["z0_plates"],o["z1_plates"])==(
                half_up(src["x0"]*w),half_up(src["x1"]*w),
                half_up((1-src["y1"])*scale),half_up((1-src["y0"])*scale))

def test_precision_uses_rendered_bundle_before_local_storage():
    viewer=(FRONTEND/"viewer.js").read_text(encoding="utf-8")
    precision=(FRONTEND/"viewer-precision.js").read_text(encoding="utf-8")
    assert "window.__BRICKHOUSE_CURRENT_BUNDLE__=b" in viewer
    assert "if(window.__BRICKHOUSE_CURRENT_BUNDLE__)return window.__BRICKHOUSE_CURRENT_BUNDLE__" in precision

def test_comparison_page_exposes_controlled_four_widths():
    page=(FRONTEND/"scale-prototypes.html").read_text(encoding="utf-8")
    assert "CONTROLLED_SCALE_PROTOTYPE" in page
    for w in WIDTHS:
        assert f'data-w="{w}"' in page
    assert "viewer.html?bundle=" in page
