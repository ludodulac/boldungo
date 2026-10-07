import json
from pathlib import Path
import pytest
from brickhouse.scene import ArchitecturalScene

P=Path("frontend/data/boldungo2-guided-005e-m2-scene.json")
VIEWER=Path("frontend/scene-viewer.js")
EPS=1e-6

def raw(): return json.loads(P.read_text(encoding="utf-8"))
def ps(prefix): return [p for p in raw()["platforms"] if p["id"].startswith(prefix)]
def top(p): return p["position"]["z"]+p["thickness"]

def test_005e_canonical_and_counts_widths():
    scene=ArchitecturalScene.model_validate(raw())
    assert scene.schema_version=="0.2"
    lo,hi=ps("m2-run7-step-"),ps("m2-run9-step-")
    assert len(lo)==7 and len(hi)==9
    assert all(abs(p["depth"]-1.12)<=EPS for p in lo)
    assert all(abs(p["width"]-1.12)<=EPS for p in hi)
    assert scene.stairs==[]

def test_005e_lower_endpoint_equals_landing_entry_edge_no_gap_overlap():
    d=raw(); lo=ps("m2-run7-step-")
    L=next(p for p in d["platforms"] if p["id"]=="m2-intermediate-square-landing")
    endpoint=max(p["position"]["x"]+p["width"] for p in lo)
    entry=L["position"]["x"]
    assert endpoint == pytest.approx(entry,abs=EPS)
    assert abs(endpoint-entry)<=EPS
    # transverse bounds are exactly identical
    assert all(p["position"]["y"]==pytest.approx(L["position"]["y"],abs=EPS) for p in lo)
    assert all(p["position"]["y"]+p["depth"]==pytest.approx(L["position"]["y"]+L["depth"],abs=EPS) for p in lo)
    # contiguous lower treads: no gap and no overlap
    for a,b in zip(lo,lo[1:]):
        assert a["position"]["x"]+a["width"]==pytest.approx(b["position"]["x"],abs=EPS)

def test_005e_upper_start_equals_same_landing_exit_edge_no_gap_overlap():
    d=raw(); hi=ps("m2-run9-step-")
    L=next(p for p in d["platforms"] if p["id"]=="m2-intermediate-square-landing")
    # Upper travels toward decreasing y; its first tread's far edge is the landing exit edge.
    start=hi[0]["position"]["y"]+hi[0]["depth"]
    exit_edge=L["position"]["y"]
    assert start==pytest.approx(exit_edge,abs=EPS)
    assert abs(start-exit_edge)<=EPS
    assert all(p["position"]["x"]==pytest.approx(L["position"]["x"],abs=EPS) for p in hi)
    assert all(p["position"]["x"]+p["width"]==pytest.approx(L["position"]["x"]+L["width"],abs=EPS) for p in hi)
    for a,b in zip(hi,hi[1:]):
        assert b["position"]["y"]+b["depth"]==pytest.approx(a["position"]["y"],abs=EPS)

def test_005e_vertical_junctions_and_high_arrival_are_exact():
    d=raw(); lo=ps("m2-run7-step-"); hi=ps("m2-run9-step-")
    L=next(p for p in d["platforms"] if p["id"]=="m2-intermediate-square-landing")
    T=next(p for p in d["platforms"] if p["id"]=="m2-high-concrete-terrace")
    assert top(lo[-1])==pytest.approx(L["position"]["z"]+L["thickness"],abs=EPS)
    assert hi[0]["position"]["z"]==pytest.approx(L["position"]["z"]+L["thickness"],abs=EPS)
    assert top(hi[-1])==pytest.approx(top(T),abs=EPS)

def test_005e_parapets_rederived_on_run_bounds_and_all_baselines_horizontal():
    d=raw(); lo=ps("m2-run7-step-"); hi=ps("m2-run9-step-")
    lw=[w for w in d["partial_wall_segments"] if w["id"].startswith("m2-run7-parapet-")]
    hw=[w for w in d["partial_wall_segments"] if w["id"].startswith("m2-run9-parapet-")]
    assert len(lw)==14 and len(hw)==18
    assert all(w["start"]["z"]==pytest.approx(w["end"]["z"],abs=EPS) for w in lw+hw)
    assert min(w["start"]["x"] for w in lw)==pytest.approx(lo[0]["position"]["x"],abs=EPS)
    assert max(w["end"]["x"] for w in lw)==pytest.approx(lo[-1]["position"]["x"]+lo[-1]["width"],abs=EPS)
    assert max(w["start"]["y"] for w in hw)==pytest.approx(hi[0]["position"]["y"]+hi[0]["depth"],abs=EPS)
    assert min(w["end"]["y"] for w in hw)==pytest.approx(hi[-1]["position"]["y"],abs=EPS)

def test_005e_open_void_m3_absent_and_viewer_unchanged_contract():
    d=raw(); T=next(p for p in d["platforms"] if p["id"]=="m2-high-concrete-terrace")
    assert T["thickness"]<.5 and len(T["supports"])==2
    assert not any(p.get("material")=="timber" for p in d["platforms"])
    assert len(d["volumes"])==1 and d["volumes"][0]["id"]=="house-main-reference"
    viewer=VIEWER.read_text(encoding="utf-8")
    assert "renderVolumes(); renderOpenings(); renderPlatforms(); renderPartialWallSegments(); renderStairs();" in viewer
