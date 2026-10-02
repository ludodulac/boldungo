from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def test_browser_package_input_adapter_contract() -> None:
    completed = subprocess.run(
        ["node", "tests/analysis_package_input_v1_082b3.mjs"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "BOLDUNGO-082B3 package input adapter contract passed" in completed.stdout


def test_adapter_reads_the_real_active_project_snapshot() -> None:
    source = (ROOT / "frontend" / "analysis-package-input-v1.js").read_text(encoding="utf-8")
    assert "getActiveProjectSnapshot" in source
    assert "project-photo-store.js" in source
    assert "await getActiveProjectSnapshot()" in source
    assert "new Blob" not in source
    assert "FileReader" not in source
    assert "base64" not in source.lower()
