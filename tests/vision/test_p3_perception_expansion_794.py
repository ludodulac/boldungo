import json
from pathlib import Path

ROOT=Path(__file__).parents[2]
REQUEST=ROOT/"frontend"/"p3-perception-expansion-request-794.json"
BOOTSTRAP=ROOT/"tests"/"fixtures"/"vision"/"visual-bootstrap-response-062.json"

def test_794_is_p3_only_and_separates_existing_from_candidates():
    r=json.loads(REQUEST.read_text()); b=json.loads(BOOTSTRAP.read_text())
    assert r["request_id"]=="p3-perception-expansion-794"
    assert r["photo_index"]==3
    assert r["authorized_visual_source"]["photo_index"]==3
    assert r["authorized_visual_source"]["inspection_roi"]==[0,0,1,1]
    existing={x["observation_ref"] for x in r["existing_local_observations"]}
    actual={x["observation_id"] for x in b["observations"] if x["photo_index"]==3}
    assert existing==actual=={"obs_p3_box_volume","obs_p3_tree","obs_p3_dark_opening"}
    candidates={x["candidate_id"] for x in r["candidate_region_searches"]}
    assert not existing & candidates
    assert all("p4" not in x.lower() and "p5" not in x.lower() for x in candidates)

def test_794_response_contract_is_fail_closed_and_pixel_grounded():
    r=json.loads(REQUEST.read_text())
    assert r["allowed_outcomes"]==["LOCALIZABLE","AMBIGUOUS","NOT_OBSERVABLE"]
    props=r["response_schema"]["properties"]["region_results"]["items"]["properties"]
    required=set(r["response_schema"]["properties"]["region_results"]["items"]["required"])
    assert {"localized_roi","visible_boundaries","pixel_cues","relations","epistemic_confidence","semantic_interpretation"}<=required
    assert set(props["relations"]["items"]["properties"]["relation_token"]["enum"])==set(r["allowed_relation_tokens"])
    text=json.dumps(r)
    assert "Visual localization and semantic interpretation are separate" in text
    assert "LOCALIZABLE requires an exact normalized localized_roi" in text
    assert "SAME_PHYSICAL_OBJECT" in text
    assert "metric geometry" in text and "camera pose" in text
    assert "MUST NOT create or import a LocalObservation automatically" in text

def test_794_has_no_interview_or_workspace_import_and_no_other_visual_sources():
    r=json.loads(REQUEST.read_text())
    assert set(r)=={"schema_version","request_id","photo_index","authorized_visual_source","existing_local_observations","candidate_region_searches","allowed_outcomes","allowed_relation_tokens","allowed_epistemic_confidence","response_schema","response_invariants"}
    assert r["authorized_visual_source"]["image_path"].endswith("03-original.jpg")
    serialized=json.dumps(r).lower()
    assert "04-original" not in serialized and "05-original" not in serialized
    assert "same_physical_object" in serialized
    assert "multiViewWorkspace" not in json.dumps(r)
