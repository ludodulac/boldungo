import json
from pathlib import Path
import pytest
from brickhouse.scene import ArchitecturalScene

P=Path("frontend/data/boldungo2-guided-006-consolidated-scene.json")
EPS=1e-6

def d(): return json.loads(P.read_text(encoding="utf-8"))
def steps(data,p): return [x for x in data["platforms"] if x["id"].startswith(p)]
def top(p): return p["position"]["z"]+p["thickness"]
def rb(p):
    x0=p["position"]["x"]; x1=x0+p["width"]
    y0=p["position"]["y"]; y1=y0+p["depth"]
    z0=p["position"]["z"]; z1=z0+p["thickness"]
    return (x0,x1,z0,z1,-y1,-y0)
def overlap(a0,a1,b0,b1): return max(0,min(a1,b1)-max(a0,b0))

def test_006_architectural_scene_valid_and_confirmed_house_dimensions():
    x=d(); ArchitecturalScene.model_validate(x)
    h=x["volumes"][0]
    assert h["width"]["value"]==pytest.approx(9.30,abs=EPS)
    assert h["depth"]["value"]==pytest.approx(8.20,abs=EPS)
    assert h["width"]["source"]["kind"]=="user_provided"
    assert h["depth"]["source"]["kind"]=="user_provided"
    assert '"value": 10.0' not in P.read_text(encoding="utf-8")

def test_006_constrained_south_stair_render_space_contacts():
    x=d(); lo=steps(x,"south-run7-step-"); hi=steps(x,"south-run9-step-")
    L=next(p for p in x["platforms"] if p["id"]=="south-intermediate-landing")
    assert len(lo)==7 and len(hi)==9
    assert all(p["depth"]==pytest.approx(1.12,abs=EPS) for p in lo)
    assert all(p["width"]==pytest.approx(1.12,abs=EPS) for p in hi)
    lb,LR,ub=rb(lo[-1]),rb(L),rb(hi[0])
    # lower enters Xmin; full 1.12 transverse rendered-Z overlap
    assert lb[1]==pytest.approx(LR[0],abs=EPS)
    assert overlap(lb[4],lb[5],LR[4],LR[5])==pytest.approx(1.12,abs=EPS)
    # upper exits source Ymax -> rendered Zmin and travels +Y/WEST
    assert ub[5]==pytest.approx(LR[4],abs=EPS)
    assert overlap(ub[0],ub[1],LR[0],LR[1])==pytest.approx(1.12,abs=EPS)
    assert hi[1]["position"]["y"]>hi[0]["position"]["y"]
    for a,b in zip(hi,hi[1:]):
        assert b["position"]["y"]==pytest.approx(a["position"]["y"]+a["depth"],abs=EPS)

def test_006_upper_run_reaches_concrete_and_concrete_void_is_open():
    x=d(); hi=steps(x,"south-run9-step-")
    C=next(p for p in x["platforms"] if p["id"]=="south-concrete-platform")
    last=hi[-1]
    assert last["position"]["y"]+last["depth"]==pytest.approx(C["position"]["y"]+C["depth"],abs=EPS)
    assert top(last)==pytest.approx(top(C),abs=EPS)
    assert C["thickness"]<.5 and len(C["supports"])==2
    assert len(x["volumes"])==1  # no solid infill volume below slab
    door=next(o for o in x["openings"] if o["id"]=="south-lower-door")
    assert C["position"]["y"] <= door["offset_horizontal"] <= C["position"]["y"]+C["depth"]

def test_006_timber_terrace_is_distinct_open_and_has_west_nonrectangular_return():
    x=d(); C=next(p for p in x["platforms"] if p["id"]=="south-concrete-platform")
    M=next(p for p in x["platforms"] if p["id"]=="south-timber-deck-main")
    W=next(p for p in x["platforms"] if p["id"]=="south-timber-deck-west-return")
    assert C["material"]=="masonry" and M["material"]=="timber" and W["material"]=="timber"
    assert C["position"]["y"]+C["depth"]==pytest.approx(M["position"]["y"],abs=EPS)
    assert M["thickness"]<.5 and W["thickness"]<.5
    assert len(M["supports"])>=2 and len(W["supports"])>=1
    assert W["width"] < M["width"]
    assert W["position"]["y"]+W["depth"]==pytest.approx(8.20,abs=EPS)
    diag=next(w for w in x["partial_wall_segments"] if w["id"]=="timber-railing-west-diagonal")
    assert diag["start"]["x"] != diag["end"]["x"] and diag["start"]["y"] != diag["end"]["y"]

def test_006_south_openings_and_reveal_depth_limitation_are_preserved():
    x=d(); ids={o["id"] for o in x["openings"] if o["facade"]=="left"}
    assert {"south-high-entry","south-deep-french-door","south-upper-window","south-lower-door","south-round-stained-glass"} <= ids
    entry=next(o for o in x["openings"] if o["id"]=="south-high-entry")
    french=next(o for o in x["openings"] if o["id"]=="south-deep-french-door")
    assert "SHALLOW_REVEAL" in entry["opening_visual"]["notes"]
    assert "DEEP_REVEAL" in french["opening_visual"]["notes"]
    assert entry["opening_visual"]["notes"] != french["opening_visual"]["notes"]

def test_006_east_has_exactly_six_main_openings():
    x=d(); east=[o for o in x["openings"] if o["facade"]=="front"]
    assert len(east)==6
    assert sum(o["offset_vertical"]<2.5 for o in east)==2
    assert sum(2.5<=o["offset_vertical"]<5 for o in east)==2
    assert sum(o["offset_vertical"]>=5 for o in east)==2

def test_006_north_features_and_rising_grade():
    x=d(); north={o["id"]:o for o in x["openings"] if o["facade"]=="right"}
    assert "north-upper-window" in north and "north-glass-block" in north
    assert north["north-glass-block"]["opening_visual"]["pane_layout"]=="6 x 5 glass blocks"
    gp=next(p for p in x["terrain"]["profiles"] if p["facade"]=="right")
    assert gp["end_elevation"] > gp["start_elevation"]
    assert gp["source"]["kind"]=="inferred"
    assert any(e["id"]=="north-gas-meter-hatch" for e in x["equipment"])

def test_006_roof_chimneys_lavoir_and_provenance():
    x=d(); roof=x["roofs"][0]
    assert roof["type"]=="gable" and roof["pitch_degrees"]==22
    assert roof["source"]["kind"]=="inferred"
    assert {c["id"] for c in x["chimneys"]}=={"west-metal-chimney-volume","house-chimney-antenna"}
    lav=next(p for p in x["platforms"] if p["id"]=="south-lavoir-planter-landmark")
    assert lav["width"]==pytest.approx(1.78,abs=EPS) and lav["depth"]==pytest.approx(1.20,abs=EPS)
    assert lav["source"]["kind"]=="user_provided"

def test_006_no_confirmed_constraint_was_silently_compensated():
    x=d()
    assert x["volumes"][0]["width"]["value"]==9.3
    assert x["volumes"][0]["depth"]["value"]==8.2
    lo=steps(x,"south-run7-step-"); hi=steps(x,"south-run9-step-")
    assert len(lo)==7 and len(hi)==9
    assert all(p["depth"]==1.12 for p in lo)
    assert all(p["width"]==1.12 for p in hi)
    assert hi[-1]["position"]["y"] > hi[0]["position"]["y"]
