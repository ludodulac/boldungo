from pathlib import Path
import json

VIEWER = Path("frontend/viewer.js")
AUTONOMOUS = Path("frontend/notice-autonomous-preview-export.json")
HISTORIC = Path("frontend/notice-reconstructed-steps-1-34-export.json")


def test_viewer_loads_autonomous_preview_without_replacing_historic_notice():
    source = VIEWER.read_text(encoding="utf-8")
    preview = json.loads(AUTONOMOUS.read_text(encoding="utf-8"))
    historic = json.loads(HISTORIC.read_text(encoding="utf-8"))

    assert "noticeMode==='autonomous-preview'" in source
    assert "fetch('./notice-autonomous-preview-export.json'" in source
    assert "renderBundle(await r.json(),{persist:false});showAssemblyStep(0)" in source
    assert len(preview["assembly_plan"]["steps"]) == preview["assembly_plan"]["total_steps"] == 5
    assert preview["assembly_plan"]["steps"][0]["placement_ids"] == ["wall-000001"]

    assert "fetch('./notice-reconstructed-steps-1-34-export.json'" in source
    assert len(historic["assembly_plan"]["steps"]) == historic["assembly_plan"]["total_steps"] == 34
