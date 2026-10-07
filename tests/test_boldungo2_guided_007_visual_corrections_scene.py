import json, math
from pathlib import Path
import pytest
from brickhouse.scene import ArchitecturalScene

P6=Path("frontend/data/boldungo2-guided-006-consolidated-scene.json")
P7=Path("frontend/data/boldungo2-guided-007-visual-corrections-scene.json")
EPS=1e-6
def load(p): return json.loads(p.read_text(encoding="utf-8"))
def byid(xs,i): return next(x for x in xs if x["id"]==i)
def south_platforms(x): return [p for p in x["platforms"] if p["id"].startswith(("south-run7-","south-intermediate-","south-run9-","south-concrete-","south-timber-","south-lavoir-"))]
def south_walls(x): return [w for w in x["partial_wall_segments"] if w["id"].startswith(("south-run7-","south-run9-","timber-"))]

def test_007_valid_and_confirmed_dimensions_preserved():
    x=load(P7); ArchitecturalScene.model_validate(x)
    h=x["volumes"][0]
    assert h["width"]["value"]==pytest.approx(9.30,abs=EPS)
    assert h["depth"]["value"]==pytest.approx(8.20,abs=EPS)

def test_007_front_gable_is_objectively_lower_than_006_and_stays_inferred():
    a,b=load(P6),load(P7); r6=a["roofs"][0]; r7=b["roofs"][0]
    assert r7["type"]=="gable" and r7["source"]["kind"]=="inferred"
    assert r7["pitch_degrees"] < r6["pitch_degrees"]
    run=a["volumes"][0]["width"]["value"]/2
    assert math.tan(math.radians(r7["pitch_degrees"]))*run < math.tan(math.radians(r6["pitch_degrees"]))*run

def test_007_east_openings_form_two_vertical_axes():
    x=load(P7); o={z["id"]:z for z in x["openings"]}
    def center(i): return o[i]["offset_horizontal"]+o[i]["width"]/2
    left=[center(i) for i in ("east-rdc-window-left","east-mid-window-left","east-upper-window-left")]
    right=[center(i) for i in ("east-rdc-french-door-right","east-mid-window-right","east-upper-window-right")]
    assert max(left)-min(left)<=EPS
    assert max(right)-min(right)<=EPS
    assert left[0] < right[0]

def test_007_north_high_window_moved_from_too_centered_006():
    a,b=load(P6),load(P7)
    before=byid(a["openings"],"north-upper-window")["offset_horizontal"]
    after=byid(b["openings"],"north-upper-window")["offset_horizontal"]
    assert before==pytest.approx(3.0,abs=EPS)
    assert after==pytest.approx(1.35,abs=EPS)
    assert after != pytest.approx(before,abs=EPS)
    # preserve other north opening geometry
    assert byid(a["openings"],"north-glass-block")==byid(b["openings"],"north-glass-block")

def test_007_exactly_two_retained_chimneys_have_viewer_rendered_geometry():
    x=load(P7)
    assert {c["id"] for c in x["chimneys"]}=={"west-metal-chimney-volume","house-chimney-antenna"}
    rear=byid(x["platforms"],"render-west-metal-chimney-volume")
    house=byid(x["platforms"],"render-house-chimney")
    assert rear["material"]=="metal" and len(rear["supports"])==1
    assert house["material"]=="masonry" and len(house["supports"])==1
    rb=rear["supports"][0]; hb=house["supports"][0]
    assert rb["width"]==pytest.approx(1.5) and rb["depth"]==pytest.approx(.55) and rb["height"]==pytest.approx(5.8)
    assert rb["width"]*rb["depth"] > hb["width"]*hb["depth"]
    assert rb["height"] > hb["height"]

def test_007_north_grade_has_visible_rising_geometry_and_semantic_profile():
    x=load(P7); gp=next(p for p in x["terrain"]["profiles"] if p["facade"]=="right")
    assert gp["end_elevation"] > gp["start_elevation"]
    steps=sorted([p for p in x["platforms"] if p["id"].startswith("north-grade-step-")],key=lambda p:p["position"]["y"])
    assert len(steps)==8
    assert all(p["position"]["x"]==pytest.approx(9.30,abs=EPS) for p in steps)
    assert all(b["thickness"]>a["thickness"] for a,b in zip(steps,steps[1:]))
    assert steps[-1]["thickness"]==pytest.approx(gp["end_elevation"],abs=EPS)

def test_007_south_system_is_byte_for_byte_geometrically_unchanged_from_006():
    a,b=load(P6),load(P7)
    assert south_platforms(a)==south_platforms(b)
    assert south_walls(a)==south_walls(b)
    lo=[p for p in south_platforms(b) if p["id"].startswith("south-run7-step-")]
    hi=[p for p in south_platforms(b) if p["id"].startswith("south-run9-step-")]
    assert len(lo)==7 and len(hi)==9
    assert all(p["depth"]==pytest.approx(1.12,abs=EPS) for p in lo)
    assert all(p["width"]==pytest.approx(1.12,abs=EPS) for p in hi)
    assert all(bb["position"]["y"]>aa["position"]["y"] for aa,bb in zip(hi,hi[1:]))
    C=byid(b["platforms"],"south-concrete-platform")
    M=byid(b["platforms"],"south-timber-deck-main")
    assert C["material"]=="masonry" and M["material"]=="timber"
    assert C["thickness"]<.5 and M["thickness"]<.5
    assert len(C["supports"])==2 and len(M["supports"])>=2

def test_007_no_viewer_or_contract_dependency_encoded_in_scene():
    x=load(P7)
    assert x["schema_version"]=="0.2"
    assert x["stairs"]==[]
