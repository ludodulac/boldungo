from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def read(name: str) -> str:
    return (FRONTEND / name).read_text(encoding="utf-8")


def test_sophie_r001_result_runtime_contract() -> None:
    completed = subprocess.run(
        ["node", "tests/analysis_result_import_v1_082b6.mjs"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "BOLDUNGO-082B6 Sophie R001 RESULT import contract passed" in completed.stdout


def test_v1_result_import_is_registered_before_legacy_import_routes() -> None:
    package = read("brickhouse-survey-package.js")
    assert "analysis-result-import-v1.js?v=exchange-v1-sophie-r001-result" in package

    controller = read("analysis-result-import-v1.js")
    assert "event.preventDefault()" in controller
    assert "event.stopImmediatePropagation()" in controller
    assert "if (!isBoldungoExchangeV1(parsed))" in controller
    assert "return;" in controller
    assert "{ capture: true }" in controller


def test_result_persistence_uses_project_indexeddb_without_touching_exports() -> None:
    store = read("project-photo-store.js")
    assert "analysis_result_imports: []" in store
    assert "export async function appendAnalysisResultImport" in store
    assert "database.transaction(STORE_PROJECTS, 'readwrite')" in store
    assert "document: structuredClone(document)" in store
    assert "analysis_result_imports:" in store

    start = store.index("export async function appendAnalysisResultImport(")
    end = store.index("export async function getActiveProjectSnapshot()", start)
    persistence_block = store[start:end]
    assert "analysis_package_exports =" not in persistence_block
    assert "analysis_package_exports:" not in persistence_block


def test_browser_validator_is_local_and_analysis_result_only() -> None:
    validator = read("analysis-result-validator-v1.js")
    assert "ANALYSIS_RESULT" in validator
    assert "HUMAN_ANSWERS" not in validator
    assert "fetch(" not in validator
    assert "http://" not in validator.lower()
    assert "https://" not in validator.lower()
    assert "relation symétrique dupliquée" in validator
    assert "resolved_by_human_fact_refs" in validator
    assert "resolved_by_observation_refs" in validator
    assert "source_round_id" in validator
    assert "uncertainty_refs" in validator
