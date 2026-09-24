import json
from pathlib import Path

REQUEST=Path("frontend/spatial-pixel-check-request-788.json")

def test_788_request_is_bounded_structured_and_pixel_grounded():
    d=json.loads(REQUEST.read_text())
    assert d["request_id"]=="spatial-pixel-check-788"
    assert d["organization_ref"]=="org_rear_sector_787"
    assert d["allowed_photos"]==[3,4,5]
    assert {x["photo_index"] for x in d["observations"]}=={3,4,5}
    assert {x["photo_index"] for x in d["spatial_tests"]}=={3,4,5}
    assert len(d["spatial_tests"])==6
    assert d["allowed_verdict_tokens"]==["SUPPORTED","CONTRADICTED","AMBIGUOUS","NOT_OBSERVABLE"]
    known={x["observation_ref"] for x in d["observations"]}
    assert all(set(t["observation_refs"]) <= known for t in d["spatial_tests"])
    assert all(len(x["roi"])==4 and all(0<=v<=1 for v in x["roi"]) for x in d["observations"])
    invariants=" ".join(d["response_invariants"])
    assert "coexistence alone is insufficient" in invariants
    assert "never a contradiction" in invariants
    assert "Do not infer SAME_PHYSICAL_OBJECT" in invariants
    schema=d["response_schema"]
    assert schema["properties"]["request_id"]["const"]=="spatial-pixel-check-788"
    assert schema["properties"]["results"]["minItems"]==6
    assert schema["properties"]["results"]["maxItems"]==6
