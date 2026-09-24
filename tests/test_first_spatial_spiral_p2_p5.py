import json
from pathlib import Path

ROOT=Path(__file__).parents[1]
ARTIFACT=ROOT/"frontend"/"spatial-spiral-p2-p5.json"
RESPONSE=ROOT/"frontend"/"spatial-pixel-check-response-788.json"

def test_789_visual_artifact_is_fail_closed_and_matches_imported_788():
    d=json.loads(ARTIFACT.read_text())
    r=json.loads(RESPONSE.read_text())
    assert d["artifact_id"]=="p3-perception-ingestion-795"
    assert d["observer_import"]["request_id"]=="spatial-pixel-check-788"
    assert d["view_explanation_gain"]["invented_geometry_added"] is False
    assert len(d["organizations"])==1
    o=d["organizations"][0]
    assert o["id"]=="org_rear_sector_787"
    assert o["epistemic_level"]=="CANDIDATE"
    expected={x["test_id"]:(x["verdict"],x["relation_tokens"]) for x in r["results"]}
    actual={x["prediction_id"]:(x["verdict"],x["relations"]) for x in o["predictions"]}
    assert actual==expected
    assert d["view_explanation_gain"]["positive_spatial_consequence_photo_indexes"]==[3,4,5]
    assert set(d["view_explanation_gain"]["ambiguous_constraint_ids"])=={"788-p3-visible-junctions","788-p4-wall-platform"}
    assert d["view_explanation_gain"]["not_observable_constraint_ids"]==["788-p4-stair-platform"]
    unresolved=" ".join(o["unresolved"])
    assert "physical identity" in unresolved
    assert "NOT_OBSERVABLE" in unresolved
    assert "AMBIGUOUS" in unresolved
    assert "metric geometry UNKNOWN" in unresolved
    assert "SAME_PHYSICAL_OBJECT" in d["note"]
    t=d["inter_view_discriminant_790"]
    assert t["outcome"]=="AMBIGUOUS" and t["uncertainty_state"]=="OPEN"
    assert t["acquired_local_constraint"]["relation_token"]=="BELOW"
    assert t["identity_acquired"] is False and t["invented_geometry_added"] is False
    u=d["inter_view_discriminant_792"]
    assert u["outcome"]=="CORRESPONDENCE_COMPATIBLE"
    assert u["uncertainty_state"]=="LOCAL_COMPATIBILITY_ESTABLISHED"
    assert u["physical_identity"]=="UNRESOLVED"
    assert u["identity_acquired"] is False and u["invented_geometry_added"] is False
    assert {r for x in u["acquired_local_constraints"] for r in x["relations"]}=={"CONTAINED_WITHIN","BELOW"}
