import json
from pathlib import Path

ROOT=Path(__file__).parents[2]
REQUEST=ROOT/"frontend"/"interview-discriminant-request-790.json"

def test_790_interview_discriminant_request_is_bounded_and_fail_closed():
    r=json.loads(REQUEST.read_text())
    assert r["request_id"]=="interview-discriminant-790"
    assert r["organization_ref"]=="org_rear_sector_787"
    assert r["source_uncertainty"]["kind"]=="INTER_VIEW_SECTOR_CORRESPONDENCE"
    assert r["source_uncertainty"]["priority_state"]=="TIED_MINIMAL_CHOICE"
    assert r["authorized_photos"]==[4,5]
    assert {o["observation_ref"] for o in r["authorized_observations"]}=={
        "obs_p4_rear_wall","obs_p4_upper_window","obs_p5_side_wall","obs_p5_near_window","obs_p5_roof_edge"
    }
    alternatives={x["token"] for x in r["hypotheses_or_alternatives"]}
    assert alternatives=={"LOCAL_LAYOUT_CORRESPONDENCE_COMPATIBLE","LOCAL_LAYOUT_CORRESPONDENCE_INCOMPATIBLE"}
    assert set(r["allowed_outcomes"])=={"CORRESPONDENCE_COMPATIBLE","CORRESPONDENCE_INCOMPATIBLE","AMBIGUOUS","NOT_OBSERVABLE"}
    assert len(r["discriminating_properties"])>=2
    schema=r["response_schema"]
    assert schema["properties"]["request_id"]["const"]==r["request_id"]
    assert schema["properties"]["source_uncertainty_id"]["const"]==r["source_uncertainty"]["uncertainty_id"]
    assert schema["properties"]["organization_ref"]["const"]==r["organization_ref"]
    invariants=" ".join(r["response_invariants"])
    assert "SAME_PHYSICAL_OBJECT" in invariants
    assert "Visual similarity alone" in invariants
    assert "AMBIGUOUS" in invariants and "NOT_OBSERVABLE" in invariants
    assert "metric geometry" in invariants
