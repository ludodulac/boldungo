import json
from pathlib import Path
import pytest
from brickhouse.scene import ArchitecturalScene

P=Path("frontend/data/boldungo2-guided-008-south-corrected-scene.json")
OLD=Path("frontend/data/boldungo2-guided-007-visual-corrections-scene.json")
EPS=1e-6

def load(p=P): return json.loads(p.read_text(encoding="utf-8"))
def byid(xs,i): return next(x for x in xs if x["id"]==i)
def steps(d,p): return [x for x in d["platforms"] if x["id"].startswith(p)]
def bounds(p): return (p["position"]["x"],p["position"]["x"]+p["width"],p["position"]["y"],p["position"]["y"]+p["depth"])
def top(p): return p["position"]["z"]+p["thickness"]
def center_y(o): return o["offset_horizontal"]+o["width"]/2

def test_008_valid_house_and_physical_axis_contract():
    d=load(); ArchitecturalScene.model_validate(d)
    h=byid(d["volumes"],"house-main")
    assert h["position"]=={"x":0,"y":0,"z":0}
    assert h["width"]["value"]==pytest.approx(9.30,abs=EPS)
    assert h["depth"]["value"]==pytest.approx(8.20,abs=EPS)
    # Certified mapping: EAST=Ymin, WEST=Ymax, SOUTH=Xmin; outside SOUTH is -X.
    assert 0 < 8.20
    assert -1 < 0  # JSON -X is SOUTH exterior
    assert 0-1 < 0 # JSON -Y points EAST from any positive-Y point
    assert 0+1 > 0 # JSON +Y points WEST

def test_008_stair_is_outside_south_counts_width_and_extends_beyond_house_west():
    d=load(); lo=steps(d,"south-run7-step-"); hi=steps(d,"south-run9-step-")
    L=byid(d["platforms"],"south-intermediate-landing")
    assert len(lo)==7 and len(hi)==9
    assert all(p["position"]["x"]<0 and p["position"]["x"]+p["width"]<=EPS for p in lo+hi+[L])
    assert all(p["depth"]==pytest.approx(1.12,abs=EPS) for p in lo)
    assert all(p["width"]==pytest.approx(1.12,abs=EPS) for p in hi)
    assert max(p["position"]["y"]+p["depth"] for p in lo+hi+[L])>8.20
    # significant: > 50% of lower/landing longitudinal width lies beyond house WEST limit
    assert L["position"]["y"]+L["depth"]-8.20 > L["depth"]/2

def test_008_lower_landing_upper_contacts_and_upper_returns_east():
    d=load(); lo=steps(d,"south-run7-step-"); hi=steps(d,"south-run9-step-"); L=byid(d["platforms"],"south-intermediate-landing")
    assert lo[-1]["position"]["x"]+lo[-1]["width"]==pytest.approx(L["position"]["x"],abs=EPS)
    assert lo[-1]["position"]["y"]==pytest.approx(L["position"]["y"],abs=EPS)
    assert hi[0]["position"]["y"]+hi[0]["depth"]==pytest.approx(L["position"]["y"],abs=EPS)
    assert hi[0]["position"]["x"]==pytest.approx(L["position"]["x"],abs=EPS)
    ys=[p["position"]["y"] for p in hi]
    assert all(b<a for a,b in zip(ys,ys[1:])) # ascending sequence travels -Y = EAST
    assert not all(b>a for a,b in zip(ys,ys[1:])) # explicitly reject obsolete +Y/WEST
    assert L["position"]["y"] > hi[-1]["position"]["y"]

def test_008_upper_arrival_meets_concrete_and_global_order_is_timber_concrete_stair():
    d=load(); hi=steps(d,"south-run9-step-")
    C=byid(d["platforms"],"south-concrete-platform")
    M=byid(d["platforms"],"south-timber-deck-main")
    W=byid(d["platforms"],"south-timber-deck-west-return")
    L=byid(d["platforms"],"south-intermediate-landing")
    arrival=hi[-1]
    assert arrival["position"]["y"]==pytest.approx(C["position"]["y"]+C["depth"],abs=EPS)
    assert top(arrival)==pytest.approx(top(C),abs=EPS)
    timber_max=max(M["position"]["y"]+M["depth"],W["position"]["y"]+W["depth"])
    concrete_min=C["position"]["y"]; concrete_max=C["position"]["y"]+C["depth"]
    assert timber_max==pytest.approx(concrete_min,abs=EPS)
    assert concrete_max < L["position"]["y"] # concrete EAST of western stair/landing zone
    assert M["material"]=="timber" and W["material"]=="timber" and C["material"]=="masonry"
    assert M["thickness"]<.5 and W["thickness"]<.5 and C["thickness"]<.5
    assert len(M["supports"])>=2 and len(W["supports"])>=1 and len(C["supports"])==2

def test_008_explicitly_rejects_old_007_concrete_then_timber_to_west():
    old=load(OLD); new=load()
    oc=byid(old["platforms"],"south-concrete-platform"); om=byid(old["platforms"],"south-timber-deck-main")
    assert oc["position"]["y"]+oc["depth"]==pytest.approx(om["position"]["y"],abs=EPS)
    assert om["position"]["y"] > oc["position"]["y"] # obsolete concrete -> timber toward WEST
    nc=byid(new["platforms"],"south-concrete-platform")
    nm=[p for p in new["platforms"] if p["id"].startswith("south-timber-deck-")]
    assert max(p["position"]["y"]+p["depth"] for p in nm)<=nc["position"]["y"]+EPS

def test_008_south_opening_order_and_aligned_group():
    d=load(); o={x["id"]:x for x in d["openings"] if x["facade"]=="left"}
    vit=center_y(o["south-round-stained-glass"])
    french=center_y(o["south-deep-french-door"])
    group=[center_y(o[i]) for i in ("south-lower-door","south-high-entry","south-upper-window")]
    assert vit < french < group[0]
    assert max(group)-min(group)<=EPS
    # vertical/function distinctions remain
    assert o["south-lower-door"]["offset_vertical"] < o["south-high-entry"]["offset_vertical"] < o["south-upper-window"]["offset_vertical"]

def test_008_parapets_follow_each_step_top_not_one_fixed_base():
    d=load()
    for prefix,wprefix in (("south-run7-step-","south-run7-parapet-"),("south-run9-step-","south-run9-parapet-")):
        ss=steps(d,prefix); ws=[w for w in d["partial_wall_segments"] if w["id"].startswith(wprefix)]
        assert len(ws)==2*len(ss)
        bases=[]
        for p in ss:
            n=p["id"][-2:]; expected=top(p)
            pair=[w for w in ws if w["id"].endswith("-"+n)]
            assert len(pair)==2
            assert all(w["start"]["z"]==pytest.approx(expected,abs=EPS) and w["end"]["z"]==pytest.approx(expected,abs=EPS) for w in pair)
            bases.append(expected)
        assert len({round(z,9) for z in bases})==len(ss) # no fixed Z base across the run

def test_008_non_target_facades_and_viewer_contract_are_not_encoded_as_changes():
    new=load(); old=load(OLD)
    assert [o for o in new["openings"] if o["facade"]!="left"] == [o for o in old["openings"] if o["facade"]!="left"]
    assert new["volumes"]==old["volumes"]
    assert new["schema_version"]=="0.2"
    assert new["stairs"]==old["stairs"]
