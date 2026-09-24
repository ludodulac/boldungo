import json
from pathlib import Path

def test_spatial_organization_787_visual_artifact_is_fail_closed():
    d=json.loads(Path("frontend/spatial-spiral-p2-p5.json").read_text())
    assert d["artifact_id"]=="spatial-organization-787"
    assert d["view_explanation_gain"]["invented_geometry_added"] is False
    assert len(d["organizations"])==1
    org=d["organizations"][0]
    assert org["epistemic_level"]=="CANDIDATE"
    verdicts={x["photo_index"]:x["verdict"] for x in org["predictions"]}
    assert verdicts=={3:"AMBIGUOUS",4:"SUPPORTED",5:"AMBIGUOUS",2:"NOT_OBSERVABLE"}
    assert d["view_explanation_gain"]["contradicted_prediction_ids"]==[]
    assert "metric geometry UNKNOWN" in d["surviving_small_world"]["unresolved"]
