from pathlib import Path
import json
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_clarification_engine_node_contract() -> None:
    node = shutil.which("node")
    assert node, "Node.js is required for clarification engine contract tests"
    completed = subprocess.run(
        [node, str(ROOT / "tests" / "clarification_engine_081c.mjs")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "BOLDUNGO-081C clarification engine contract passed" in completed.stdout


def test_clarification_state_reuses_project_persistence() -> None:
    store = read("frontend/project-photo-store.js")
    assert "clarifications: []" in store
    assert "human_facts: []" in store
    assert "updateProjectClarificationState" in store
    assert "clarifications: structuredClone(clarifications)" in store
    assert "human_facts: structuredClone(humanFacts)" in store
    assert "clarification_fixture_id" in store
    assert "localStorage" not in store


def test_real_house_5_fixture_is_local_and_not_universal() -> None:
    fixture_path = FRONTEND / "benchmarks" / "real-house-5" / "clarifications-v1.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    assert fixture["fixture_id"] == "real-house-5-081"
    ids = {item["clarification_id"] for item in fixture["clarifications"]}
    assert ids == {
        "A01_TARGET_BOUNDARY",
        "A02_CHIMNEY_OWNERSHIP",
        "A02B_CHIMNEY_IDENTIFICATION",
        "A03_STAIR_TOPOLOGY",
        "A04_STAIR_UNDERSIDE",
        "A05_PLATFORM_UNDERSIDE",
        "A06_HIGH_ACCESS_OPENING",
        "A07_THRESHOLD_LEVEL",
        "A08_MASONRY_TO_TIMBER_CONTINUITY",
        "A09_ROOF_MATERIAL",
    }
    store = read("frontend/project-photo-store.js")
    runtime = read("frontend/photo-capture-runtime.js")
    assert "A03_STAIR_TOPOLOGY" not in store
    assert "A03_STAIR_TOPOLOGY" not in runtime


def test_lab_is_explicit_deterministic_local_mode() -> None:
    html = read("frontend/photo.html")
    lab = read("frontend/clarification-lab.js")
    engine = read("frontend/clarification-engine.js")
    assert 'id="clarification-lab"' in html
    assert "clarification-lab.js" in html
    assert "params.get('clarification-lab') === 'real-house-5'" in lab
    assert "./benchmarks/real-house-5/clarifications-v1.json" in lab
    assert "updateProjectClarificationState" in lab
    assert "activeQuestionQueue" in lab
    assert "evaluateClarificationGate" in lab
    assert "fetch('./benchmarks/real-house-5/clarifications-v1.json'" in lab
    forbidden = ("openai", "anthropic", "gemini", "llm", "api.openai", "vision api")
    combined = (lab + engine).lower()
    for marker in forbidden:
        assert marker not in combined
    assert "https://" not in lab
    assert "http://" not in lab
