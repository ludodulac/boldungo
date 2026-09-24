import json
from pathlib import Path

ROOT=Path(__file__).parents[2]
REQUEST=ROOT/"frontend"/"composite-interview-discriminant-request-796.json"
BOOTSTRAP=ROOT/"tests"/"fixtures"/"vision"/"visual-bootstrap-response-062.json"
P3_RESPONSE=ROOT/"frontend"/"p3-perception-expansion-response-794.json"
OLD790=ROOT/"frontend"/"interview-discriminant-request-790.json"
OLD792=ROOT/"frontend"/"interview-discriminant-request-792.json"

def _r(): return json.loads(REQUEST.read_text())

def test_796_uses_only_persistent_minimal_p3_p4_observations_and_exact_rois():
    r=_r(); b=json.loads(BOOTSTRAP.read_text()); p3=json.loads(P3_RESPONSE.read_text())
    known={x["observation_id"]:(x["photo_index"],x["roi"]) for x in b["observations"]}
    promoted={"p3-candidate-step-diagonal-region":"obs_p3_step_diagonal_794",
              "p3-candidate-raised-platform-region":"obs_p3_raised_platform_794",
              "p3-candidate-visible-junction-region":"obs_p3_visible_junction_794"}
    for x in p3["region_results"]:
        if x["candidate_id"] in promoted: known[promoted[x["candidate_id"]]]=(3,x["localized_roi"])
    assert r["authorized_photos"]==[3,4]
    refs={x["observation_ref"] for x in r["authorized_observations"]}
    assert refs=={"obs_p3_step_diagonal_794","obs_p3_visible_junction_794","obs_p3_raised_platform_794","obs_p4_stair","obs_p4_terrace"}
    for x in r["authorized_observations"]: assert (x["photo_index"],x["roi"])==known[x["observation_ref"]]

def test_796_is_composite_independent_and_does_not_repeat_790_792():
    r=_r(); a=json.loads(OLD790.read_text()); b=json.loads(OLD792.read_text())
    props={x["property_token"] for x in r["discriminating_properties"]}
    assert len(props)>=2
    assert props.isdisjoint({x["property_token"] for x in a["discriminating_properties"]})
    assert props.isdisjoint({x["property_token"] for x in b["discriminating_properties"]})
    assert {x["request_id"] for x in r["anti_repeat_memory"]}=={"interview-discriminant-790","interview-discriminant-792"}
    assert all(x["exhausted"] is True for x in r["anti_repeat_memory"])

def test_796_withheld_wall_identity_geometry_and_auto_import_are_forbidden():
    r=_r(); text=json.dumps(r)
    refs={x["observation_ref"] for x in r["authorized_observations"]}
    assert "p3-candidate-adjacent-wall-region" not in refs
    assert r["withheld_memory"]["status"]=="WITHHELD"
    assert r["allowed_outcomes"]==["CORRESPONDENCE_COMPATIBLE","CORRESPONDENCE_INCOMPATIBLE","AMBIGUOUS","NOT_OBSERVABLE"]
    assert "Never answer SAME_PHYSICAL_OBJECT, LIKELY_SAME or DISTINCT_PHYSICAL_OBJECTS" in text
    assert "metric geometry" in text and "camera pose" in text
    assert "No response is imported automatically" in text

def test_796_requires_pixel_provenance_and_distinguishes_ambiguous_not_observable():
    r=_r()
    assert r["mandatory_pixel_provenance"]=={"photo_index":True,"roi":True,"observation_refs":True,"pixel_cues":True,"property_token":True}
    schema=r["response_schema"]; item=schema["properties"]["provenance"]["items"]
    assert set(item["required"])=={"photo_index","roi","observation_refs","pixel_cues","property_token"}
    assert item["properties"]["pixel_cues"]["minItems"]==1
    assert schema["properties"]["property_results"]["minItems"]==3
    assert any("AMBIGUOUS and NOT_OBSERVABLE are distinct" in x for x in r["response_invariants"])
