import json
from pathlib import Path

def test_first_spatial_spiral_is_fail_closed():
    p=Path("frontend/spatial-spiral-p2-p5.json")
    d=json.loads(p.read_text())
    assert d["view_explanation_gain"]["invented_geometry_added"] is False
    org={x["id"]:x for x in d["organizations"]}
    assert org["org_legacy_p2_stair_box"]["revision"]=="REJECTED_BY_PIXELS"
    assert org["org_shared_rear_sector"]["revision"]=="SURVIVES"
    assert "Exact metric depth and dimensions" in d["surviving_small_world"]["unresolved"]
    assert all(x["check"]=="SUPPORTED" for x in org["org_shared_rear_sector"]["predictions"])
