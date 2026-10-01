from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
VIEWER = ROOT / "frontend" / "viewer.js"
BUNDLE = ROOT / "frontend" / "notice-autonomous-preview-export.json"


def test_construction_fixture_exposes_real_multiple_steps() -> None:
    bundle = json.loads(BUNDLE.read_text(encoding="utf-8"))
    plan = bundle["assembly_plan"]
    assert len(plan["steps"]) == 5
    assert plan["total_steps"] == 5
    assert plan["steps"][0]["placement_ids"]
    assert plan["steps"][1]["placement_ids"]


def test_construction_hud_renders_parts_and_real_plan_counter() -> None:
    source = VIEWER.read_text(encoding="utf-8")
    assert "depth=9,color=semanticColorValue" in source
    assert "list.replaceChildren" in source
    assert "constructionPartPreview(row.part,row.quantity)" in source
    assert "counter.textContent=`Étape ${step.sequence} / ${p.total_steps}`" in source
    assert "qty.textContent='×'+quantity" in source


def test_construction_mode_preserves_technical_viewer_and_uses_existing_framing() -> None:
    source = VIEWER.read_text(encoding="utf-8")
    configure = source.split("function configureAssembly", 1)[1].split("function constructionPartPreview", 1)[0]
    assert "showFullModel();" in configure
    assert "showAssemblyStep(0);" not in configure
    assert "if(constructionMode)showAssemblyStep(0)" in source
    assert "frameNoticePlacements([...prev,...cur],'perspective',1.18)" in source
    assert "ground.visible=!constructionMode" in source
    assert "constructionMode&&s==='previous'?'normal':s" in source
