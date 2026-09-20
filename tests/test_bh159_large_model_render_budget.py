from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEWER = ROOT / "frontend" / "viewer.js"


def test_large_exports_disable_individual_stud_meshes_only() -> None:
    source = VIEWER.read_text(encoding="utf-8")
    assert "let studMeshBudgetEnabled=true" in source
    assert "studMeshBudgetEnabled=b.brick_model.parts.length<=1200" in source
    assert "studMeshBudgetEnabled&&(studDetailEnabled||span<=4)" in source
    assert "studMeshBudgetEnabled&&(noticeFirstStep||studDetailEnabled||w*l<=4)" in source


def test_large_model_budget_does_not_change_export_data() -> None:
    source = VIEWER.read_text(encoding="utf-8")
    budget_assignment = source.index("studMeshBudgetEnabled=b.brick_model.parts.length<=1200")
    persist_assignment = source.index("localStorage.setItem('brickhouse.currentExport',JSON.stringify(b))")
    assert budget_assignment < persist_assignment
    assert "b.brick_model.parts=" not in source
    assert "b.bom=" not in source
    assert "b.assembly_plan=" not in source
