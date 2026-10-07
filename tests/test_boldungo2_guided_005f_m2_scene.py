import json
from pathlib import Path
import pytest
from brickhouse.scene import ArchitecturalScene

NEW=Path("frontend/data/boldungo2-guided-005f-m2-scene.json")
OLD=Path("frontend/data/boldungo2-guided-005e-m2-scene.json")
EPS=1e-6

def load(p): return json.loads(p.read_text(encoding="utf-8"))
def steps(d,prefix): return [p for p in d["platforms"] if p["id"].startswith(prefix)]
def src_bounds(p):
    return (p["position"]["x"],p["position"]["x"]+p["width"],p["position"]["y"],p["position"]["y"]+p["depth"],p["position"]["z"],p["position"]["z"]+p["thickness"])
def rendered_bounds(p):
    # exact renderPlatforms convention: source (x,y,z)->Three (x,z,y), centered BoxGeometry,
    # then group.scale.z=-1. Returned order: Xmin,Xmax,Ymin,Ymax,Zmin,Zmax.
    x0,x1,y0,y1,z0,z1=src_bounds(p)
    return (x0,x1,z0,z1,-y1,-y0)
def overlap(a0,a1,b0,b1): return max(0.0,min(a1,b1)-max(a0,b0))

def topology_signature(d):
    lo,hi=steps(d,"m2-run7-step-"),steps(d,"m2-run9-step-")
    L=next(p for p in d["platforms"] if p["id"]=="m2-intermediate-square-landing")
    lb,LR,ub=rendered_bounds(lo[-1]),rendered_bounds(L),rendered_bounds(hi[0])
    # Correct turn: lower contacts landing on rendered Xmin; upper leaves landing from source Ymax,
    # which is rendered Zmin after the global Z mirror.
    return {
      "lower_normal_gap": abs(lb[1]-LR[0]),
      "lower_transverse": overlap(lb[4],lb[5],LR[4],LR[5]),
      "upper_normal_gap": abs(ub[5]-LR[4]), # upper rendered Zmax touches landing rendered Zmin
      "upper_transverse": overlap(ub[0],ub[1],LR[0],LR[1]),
      "upper_on_expected_exit": abs(ub[5]-LR[4])<=EPS,
    }

def test_005f_scene_valid_counts_and_widths():
    d=load(NEW); ArchitecturalScene.model_validate(d)
    lo,hi=steps(d,"m2-run7-step-"),steps(d,"m2-run9-step-")
    assert len(lo)==7 and len(hi)==9
    assert all(p["depth"]==pytest.approx(1.12,abs=EPS) for p in lo)
    assert all(p["width"]==pytest.approx(1.12,abs=EPS) for p in hi)

def test_005f_render_space_contacts_match_entry_exit_and_turn_corner():
    d=load(NEW); s=topology_signature(d)
    assert s["lower_normal_gap"]<=EPS
    assert s["upper_normal_gap"]<=EPS
    assert s["lower_transverse"]==pytest.approx(1.12,abs=EPS)
    assert s["upper_transverse"]==pytest.approx(1.12,abs=EPS)
    L=next(p for p in d["platforms"] if p["id"]=="m2-intermediate-square-landing")
    # ENTRY=Xmin, EXIT=Ymax, TURN_CORNER=(Xmin,Ymax)
    assert steps(d,"m2-run7-step-")[-1]["position"]["x"]+steps(d,"m2-run7-step-")[-1]["width"]==pytest.approx(L["position"]["x"],abs=EPS)
    assert steps(d,"m2-run9-step-")[0]["position"]["y"]==pytest.approx(L["position"]["y"]+L["depth"],abs=EPS)
    assert steps(d,"m2-run9-step-")[0]["position"]["x"]==pytest.approx(L["position"]["x"],abs=EPS)

def test_005f_explicitly_rejects_005e_wrong_exit_edge():
    old=load(OLD); L=next(p for p in old["platforms"] if p["id"]=="m2-intermediate-square-landing")
    first=steps(old,"m2-run9-step-")[0]
    # 005E starts from Ymin and travels -Y. Correct topology requires first tread Ymin == landing Ymax and +Y travel.
    assert first["position"]["y"]+first["depth"]==pytest.approx(L["position"]["y"],abs=EPS)
    assert abs(first["position"]["y"]-(L["position"]["y"]+L["depth"]))>EPS
    old_hi=steps(old,"m2-run9-step-")
    assert old_hi[1]["position"]["y"] < old_hi[0]["position"]["y"]

def test_005f_upper_direction_is_positive_y_without_post_offset_and_hits_terrace():
    d=load(NEW); hi=steps(d,"m2-run9-step-")
    assert all(b["position"]["y"]==pytest.approx(a["position"]["y"]+a["depth"],abs=EPS) for a,b in zip(hi,hi[1:]))
    T=next(p for p in d["platforms"] if p["id"]=="m2-high-concrete-terrace")
    last=hi[-1]
    assert last["position"]["y"]+last["depth"]==pytest.approx(T["position"]["y"]+T["depth"],abs=EPS)
    assert last["position"]["z"]+last["thickness"]==pytest.approx(T["position"]["z"]+T["thickness"],abs=EPS)

def test_005f_parapets_follow_corrected_runs_and_open_void_remains():
    d=load(NEW); hi=steps(d,"m2-run9-step-")
    hw=[w for w in d["partial_wall_segments"] if w["id"].startswith("m2-run9-parapet-")]
    assert len(hw)==18
    assert all(w["start"]["z"]==pytest.approx(w["end"]["z"],abs=EPS) for w in hw)
    assert min(w["start"]["y"] for w in hw)==pytest.approx(hi[0]["position"]["y"],abs=EPS)
    assert max(w["end"]["y"] for w in hw)==pytest.approx(hi[-1]["position"]["y"]+hi[-1]["depth"],abs=EPS)
    T=next(p for p in d["platforms"] if p["id"]=="m2-high-concrete-terrace")
    assert T["thickness"]<.5 and len(T["supports"])==2
    assert d["stairs"]==[]
    assert not any(p.get("material")=="timber" for p in d["platforms"])
