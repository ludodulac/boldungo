import json
from pathlib import Path
import pytest
from brickhouse.scene import ArchitecturalScene

P = Path("frontend/data/boldungo-neutral-001-v2-scene.json")
EPS = 1e-6

def load():
    return json.loads(P.read_text(encoding="utf-8"))

def byid(items, ident):
    return next(x for x in items if x["id"] == ident)

def center(o):
    return o["offset_horizontal"] + o["width"] / 2

def test_neutral_001_contract_and_provenance():
    x = load()
    ArchitecturalScene.model_validate(x)
    assert "HOUSE_PHYSICAL_TOPOLOGY — NEUTRAL ANALYSIS V2" in x["notes"]
    assert "No geometry from historical scenes 004/005/006/007/008 was reused" in x["notes"]
    assert "FRONT=EAST" in x["notes"] and "RIGHT=NORTH" in x["notes"] and "LEFT=SOUTH" in x["notes"]

def test_confirmed_plan_dimensions_only():
    x=load(); h=x["volumes"][0]
    assert h["width"]["value"] == pytest.approx(9.30, abs=EPS)
    assert h["depth"]["value"] == pytest.approx(8.20, abs=EPS)
    assert h["width"]["source"]["kind"]=="user_provided"
    assert h["depth"]["source"]["kind"]=="user_provided"

def test_east_exactly_six_main_openings_and_two_axes():
    x=load(); east=[o for o in x["openings"] if o["id"] in {"E1","E2","E3","E4","E5","E6"}]
    assert len(east)==6
    o={q["id"]:q for q in east}
    left=[center(o[i]) for i in ("E1","E3","E5")]
    right=[center(o[i]) for i in ("E2","E4","E6")]
    assert max(left)-min(left) <= EPS
    assert max(right)-min(right) <= EPS
    assert left[0] < right[0]
    direct_surround_ids = ("E1","E3","E4","E5","E6")
    for ident in direct_surround_ids:
        q = o[ident]
        assert q.get("has_decorative_surround") is True
        assert q.get("opening_visual", {}).get("surround_color") == "beige / rose"
    e2_evidence = " ".join(e["observation"] for e in o["E2"]["evidence"])
    assert "PHOTO — HOUSE_PHYSICAL_TOPOLOGY — NEUTRAL ANALYSIS V2" in e2_evidence
    assert "same beige / rose decorative surround treatment as the other East/front main openings" in e2_evidence

def test_north_grade_is_explicitly_rising_and_visibly_materialized():
    x=load(); p=next(p for p in x["terrain"]["profiles"] if p["facade"]=="right")
    assert p["end_elevation"] > p["start_elevation"]
    steps=sorted([q for q in x["platforms"] if q["id"].startswith("north-grade-visual-")],key=lambda q:q["position"]["y"])
    assert len(steps)>=2
    assert all(b["thickness"] > a["thickness"] for a,b in zip(steps,steps[1:]))

def test_south_exterior_order_east_to_west_and_distinctness():
    x=load(); wood=byid(x["platforms"],"south-wood-terrace"); concrete=byid(x["platforms"],"south-concrete-platform")
    stair=[q for q in x["platforms"] if q["id"].startswith("stair-")]
    assert wood["id"] != concrete["id"]
    assert wood["position"]["y"] + wood["depth"] < concrete["position"]["y"]
    concrete_west_edge = concrete["position"]["y"] + concrete["depth"]
    upper = [q for q in stair if q["id"].startswith("stair-upper-step-")]
    assert concrete_west_edge == pytest.approx(min(q["position"]["y"] for q in upper), abs=EPS)
    assert max(q["position"]["y"] for q in upper) < min(q["position"]["y"] for q in stair if q["id"].startswith("stair-lower-step-"))
    assert all(q["id"] not in {wood["id"],concrete["id"]} for q in stair)

def test_wood_and_concrete_are_thin_elevated_surfaces_over_voids():
    x=load(); wood=byid(x["platforms"],"south-wood-terrace"); concrete=byid(x["platforms"],"south-concrete-platform")
    assert wood["material"]=="timber" and wood["position"]["z"]>0 and wood["thickness"]<0.5
    assert concrete["material"]=="concrete" and concrete["position"]["z"]>0 and concrete["thickness"]<0.5
    assert len(wood["supports"])>=2 and len(concrete["supports"])>=2

def test_stair_is_7_landing_turn_9_and_width_confirmed():
    x=load(); lo=sorted([q for q in x["platforms"] if q["id"].startswith("stair-lower-step-")],key=lambda q:q["id"])
    hi=sorted([q for q in x["platforms"] if q["id"].startswith("stair-upper-step-")],key=lambda q:q["id"])
    landing=byid(x["platforms"],"stair-intermediate-landing")
    assert len(lo)==7 and len(hi)==9
    assert all(q["depth"]==pytest.approx(1.12,abs=EPS) for q in lo)
    assert all(q["width"]==pytest.approx(1.12,abs=EPS) for q in hi)
    assert landing["width"]==pytest.approx(1.12,abs=EPS)
    assert lo[-1]["position"]["x"] + lo[-1]["width"] == pytest.approx(landing["position"]["x"],abs=EPS)
    assert hi[0]["position"]["x"] == pytest.approx(landing["position"]["x"],abs=EPS)

def test_upper_flight_ascends_toward_east_and_arrives_at_concrete_platform():
    x=load(); hi=sorted([q for q in x["platforms"] if q["id"].startswith("stair-upper-step-")],key=lambda q:q["id"])
    concrete=byid(x["platforms"],"south-concrete-platform")
    assert all(b["position"]["y"] < a["position"]["y"] for a,b in zip(hi,hi[1:]))
    assert all(b["thickness"] > a["thickness"] for a,b in zip(hi,hi[1:]))
    east_end=hi[-1]["position"]["y"]
    concrete_west_edge=concrete["position"]["y"]+concrete["depth"]
    assert east_end == pytest.approx(concrete_west_edge,abs=EPS)
    assert hi[-1]["position"]["z"]+hi[-1]["thickness"] == pytest.approx(concrete["position"]["z"],abs=EPS)

def test_south_opening_order_and_aligned_group():
    x=load(); o={q["id"]:q for q in x["openings"]}
    stained=o["S-stained-glass"]; french=o["S-double-french-door"]
    group=[o[i] for i in ("S-ground-door","S-high-door","S-high-window")]
    assert stained["offset_horizontal"] < french["offset_horizontal"] < min(q["offset_horizontal"] for q in group)
    centers=[center(q) for q in group]
    assert max(centers)-min(centers) <= EPS
    french_evidence = " ".join(e["observation"] for e in french["evidence"])
    assert "Deep reveal relative to S-high-door is preserved semantically" in french_evidence
    assert "v0.2 has no reveal-depth metric" in french_evidence

def test_lavoir_truth_preserved_without_false_geometric_connection():
    x=load()
    assert "LAVOIR_REPRESENTATION_LIMITATION" in x["notes"]
    assert "1.78 x 1.20 m" in x["notes"]
    assert not any("lavoir" in q["id"].lower() for q in x["platforms"]+x["stairs"]+x["partial_wall_segments"])

def test_roof_is_two_pan_zinc_with_unknown_angle_preserved():
    x=load(); r=x["roofs"][0]
    assert r["type"]=="gable"
    assert x["appearance"]["roof"]["color"]=="zinc grey"
    assert r["source"]["kind"]!="user_provided"
    assert "REPRESENTATION_CHOICE" in r["evidence"][0]["observation"]

def test_two_house_chimney_structures_only_and_uncertified_placement():
    x=load()
    assert {q["id"] for q in x["chimneys"]}=={"rear-metal-zinc-structure","house-chimney-with-antenna"}
    assert all(q["source"]["kind"]!="user_provided" for q in x["chimneys"])
    assert all("REPRESENTATION_CHOICE" in q["evidence"][0]["observation"] for q in x["chimneys"])

def test_unknown_height_and_pitch_never_claimed_as_architectural_truth():
    x=load(); h=x["volumes"][0]["height"]; r=x["roofs"][0]
    assert h["source"]["kind"]!="user_provided" and "REPRESENTATION_CHOICE" in h["evidence"][0]["observation"]
    assert r["source"]["kind"]!="user_provided" and "REPRESENTATION_CHOICE" in r["evidence"][0]["observation"]
    assert h["value"] != pytest.approx(7.20,abs=EPS)
    assert r["pitch_degrees"] not in (14,22)

def test_old_scene_banned_values_are_not_certified():
    x=load()
    assert x["volumes"][0]["height"]["value"] != 7.20
    assert x["roofs"][0]["pitch_degrees"] not in {14,22}
    assert "UNKNOWN" in x["notes"] and "REPRESENTATION_CHOICE" in x["notes"]
