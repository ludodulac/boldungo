import json
from pathlib import Path

ROOT=Path(__file__).parents[2]
REQUEST=ROOT/"frontend"/"interview-discriminant-request-792.json"
BOOTSTRAP=ROOT/"tests"/"fixtures"/"vision"/"visual-bootstrap-response-062.json"
REQUEST_790=ROOT/"frontend"/"interview-discriminant-request-790.json"

def test_792_request_is_bounded_to_p3_p5_and_persistent_observations():
    r=json.loads(REQUEST.read_text())
    b=json.loads(BOOTSTRAP.read_text())
    known={x["observation_id"]:(x["photo_index"],x["roi"]) for x in b["observations"]}
    assert r["request_id"]=="interview-discriminant-792"
    assert r["organization_ref"]=="org_rear_sector_787"
    assert r["authorized_photos"]==[3,5]
    assert 1 not in r["authorized_photos"] and 2 not in r["authorized_photos"] and 4 not in r["authorized_photos"]
    refs={x["observation_ref"] for x in r["authorized_observations"]}
    assert refs=={"obs_p3_box_volume","obs_p3_dark_opening","obs_p5_side_wall"}
    for x in r["authorized_observations"]:
        assert x["observation_ref"] in known
        assert (x["photo_index"],x["roi"])==known[x["observation_ref"]]
        assert x["photo_index"] in r["authorized_photos"]

def test_792_request_forbids_identity_and_preserves_ambiguity_nonvisibility():
    r=json.loads(REQUEST.read_text())
    assert r["allowed_outcomes"]==["CORRESPONDENCE_COMPATIBLE","CORRESPONDENCE_INCOMPATIBLE","AMBIGUOUS","NOT_OBSERVABLE"]
    text=json.dumps(r)
    assert "Do not answer SAME_PHYSICAL_OBJECT, LIKELY_SAME or DISTINCT_PHYSICAL_OBJECTS" in text
    assert "NOT_OBSERVABLE remains required" in text
    assert "AMBIGUOUS remains required" in text
    assert r["provenance_required"]=={"photo_index":True,"roi":True,"observation_refs":True,"pixel_cues":True,"property_token":True}
    schema=r["response_schema"]
    assert schema["additionalProperties"] is False
    assert schema["properties"]["property_results"]["minItems"]==3
    assert schema["properties"]["property_results"]["maxItems"]==3
    assert set(schema["properties"]["provenance"]["items"]["required"])=={"photo_index","roi","observation_refs","pixel_cues","property_token"}

def test_792_is_structurally_distinct_from_exhausted_790():
    r=json.loads(REQUEST.read_text()); old=json.loads(REQUEST_790.read_text())
    assert r["source_uncertainty"]["uncertainty_id"]!=old["source_uncertainty"]["uncertainty_id"]
    assert r["authorized_photos"]!=old["authorized_photos"]
    new_props={x["property_token"] for x in r["discriminating_properties"]}
    old_props={x["property_token"] for x in old["discriminating_properties"]}
    assert new_props.isdisjoint(old_props)
    assert 3 in r["authorized_photos"]
    assert any("Do not reuse OPENING_TO_ROOF_EDGE_RELATION" in x for x in r["response_invariants"])
    assert any(x["source"]=="790/791" and "AMBIGUOUS" in x["fact"] for x in r["prior_structured_memory"])

def test_792_p5_broad_roi_cannot_be_promoted_to_new_observation_by_contract():
    r=json.loads(REQUEST.read_text())
    p5=[x for x in r["authorized_observations"] if x["photo_index"]==5]
    assert [x["observation_ref"] for x in p5]==["obs_p5_side_wall"]
    assert any("not a pre-existing lower-volume observation" in x for x in r["response_invariants"])
    assert "return NOT_OBSERVABLE" in r["discriminating_properties"][0]["instruction"]
