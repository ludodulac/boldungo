import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=ROOT/"frontend"/"recognizable-architectural-fragment-809.html"
MANIFEST=ROOT/"frontend"/"recognizable-architectural-fragment-809.json"
CONNECTIONS=ROOT/"frontend"/"architectural-connections-808.json"
HOUSE=ROOT/"frontend"/"house-assembly-806.json"
SECONDARY=ROOT/"frontend"/"terrace-stair-assembly-807.json"

def load(p): return json.loads(p.read_text(encoding="utf-8"))

def test_809_renderer_consumes_808_spec_and_806_807_sources():
    m=load(MANIFEST)
    assert m["source_spec"].endswith("architectural-connections-808.json#recognizable-fragment-spec-808")
    assert any(x.get("source","").endswith("house-assembly-806.json") for x in m["rendered_groups"])
    assert any(x.get("source","").endswith("terrace-stair-assembly-807.json") for x in m["rendered_groups"])
    assert load(CONNECTIONS)["architectural_connection_model"]["recognizable_fragment_spec"]["spec_id"]=="recognizable-fragment-spec-808"
    assert load(HOUSE)["house_shape_model"]["recognizable_gate"]=="SUPPORTED"
    assert load(SECONDARY)["terrace_shape_model"]["recognizable_gate"]=="SUPPORTED"

def test_809_house_has_six_openings_and_supported_roof_house():
    h=HTML.read_text(encoding="utf-8")
    assert sum(f'class="opening o{i}"' in h for i in range(1,7))==6
    m=load(MANIFEST)
    assert m["roof_house_connection"]["connection_ref"]=="conn808-roof-house"
    assert m["roof_house_connection"]["status"]=="SUPPORTED"

def test_809_terrace_is_constructive_not_label_only():
    h=HTML.read_text(encoding="utf-8")
    for token in ['class="rail"','class="deck approx"','class="support s1"','class="support s2"','class="support s3"']:
        assert token in h

def test_809_stair_step_count_is_display_only_not_world_truth():
    m=load(MANIFEST)
    a=m["display_constructive_approximations"][0]
    assert a["truth_class"]=="DISPLAY_CONSTRUCTIVE_APPROXIMATION"
    assert a["persisted_step_count"] is None
    assert a["world_truth_promoted"] is False
    assert load(SECONDARY)["stair_shape_model"]["unknown_components"][1]["unknown_id"]=="stair-step-count"

def test_809_unresolved_connections_remain_unresolved():
    m=load(MANIFEST)
    states={x["interface"]:x["state"] for x in m["unresolved_interfaces"]}
    assert states["HOUSE_P1↔TERRACE_BEARING_SECTOR"]=="UNRESOLVED"
    assert states["STAIR↔TERRACE"]=="UNKNOWN_CONNECTION"
    h=HTML.read_text(encoding="utf-8")
    assert 'class="gap"' in h
    assert "landing" not in h.lower()

def test_809_truth_classes_are_traceable_and_display_layout_not_world_geometry():
    m=load(MANIFEST)
    classes={c for g in m["rendered_groups"] for c in g["truth_classes"]}
    assert {"OBSERVED","PIXEL_DERIVED_NEW","CONSTRUCTIVE_APPROXIMATION","DISPLAY_CONSTRUCTIVE_APPROXIMATION","UNKNOWN"} <= classes
    assert m["display_policy"]["display_layout_is_world_geometry"] is False
    assert m["display_policy"]["metric_claims"] is False

def test_809_uses_only_public_benchmark_photos():
    m=load(MANIFEST)
    assert not m["private_assets"]
    assert set(m["public_photo_refs"])=={
      "frontend/benchmarks/real-house-5/01-original.jpg",
      "frontend/benchmarks/real-house-5/03-original.jpg",
      "frontend/benchmarks/real-house-5/04-original.jpg"}
    h=HTML.read_text(encoding="utf-8")
    assert "./benchmarks/real-house-5/01-original.jpg" in h
    assert "./benchmarks/real-house-5/03-original.jpg" in h
    assert "./benchmarks/real-house-5/04-original.jpg" in h

def test_809_does_not_reuse_784_or_claim_metric_geometry():
    blob=(HTML.read_text(encoding="utf-8")+MANIFEST.read_text(encoding="utf-8")).lower()
    assert "#784" not in blob and "784" not in blob
    assert load(MANIFEST)["display_policy"]["metric_claims"] is False

def test_809_human_validation_required_not_automatic():
    m=load(MANIFEST)
    assert m["human_visual_validation"]=="REQUIRED"
    assert m["display_policy"]["automatic_recognition_validation"] is False
    assert len(m["human_questions"])==4
