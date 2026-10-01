from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_clarification_persistence_contract() -> None:
    store = (ROOT / "frontend" / "project-photo-store.js").read_text(encoding="utf-8")
    assert "clarifications: []" in store
    assert "human_facts: []" in store
    assert "updateProjectClarificationState" in store
    assert "clarifications: structuredClone(clarifications)" in store
    assert "human_facts: structuredClone(humanFacts)" in store
    assert "clarification_fixture_id" in store
    assert "localStorage" not in store
