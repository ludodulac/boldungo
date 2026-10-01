from pathlib import Path

VIEWER = Path("frontend/viewer.js")


def test_parts_strip_reuses_existing_three_geometry() -> None:
    source = VIEWER.read_text(encoding="utf-8")
    thumb = source.split("function constructionPartPreview", 1)[1].split("function updateConstructionHud", 1)[0]
    assert "new THREE.WebGLRenderer" in thumb
    assert "piece=makePartMesh(" in thumb
    assert "new THREE.PerspectiveCamera" in thumb
    assert "qty.textContent='×'+quantity" in thumb
    assert "fillRect(" not in thumb
    assert "ctx.ellipse(" not in thumb


def test_parts_grouping_and_real_assembly_plan_are_unchanged() -> None:
    source = VIEWER.read_text(encoding="utf-8")
    hud = source.split("function updateConstructionHud", 1)[1].split("function showAssemblyStep", 1)[0]
    assert "for(const id of step.placement_ids)" in hud
    assert "const key=part.part_id+'|'+(part.semantic_color??part.category)" in hud
    assert "row.quantity++" in hud
    assert "counter.textContent=`Étape ${step.sequence} / ${p.total_steps}`" in hud


def test_technical_viewer_default_is_preserved() -> None:
    source = VIEWER.read_text(encoding="utf-8")
    configure = source.split("function configureAssembly", 1)[1].split("function constructionPartPreview", 1)[0]
    assert "showFullModel();" in configure
    assert "showAssemblyStep(0);" not in configure
