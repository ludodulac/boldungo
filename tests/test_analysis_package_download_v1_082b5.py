from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def read(name: str) -> str:
    return (FRONTEND / name).read_text(encoding="utf-8")


def test_sophie_r001_download_runtime_contract() -> None:
    completed = subprocess.run(
        ["node", "tests/analysis_package_download_v1_082b5.mjs"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "BOLDUNGO-082B5 Sophie R001 download contract passed" in completed.stdout


def test_normal_button_uses_v1_zip_and_not_legacy_pdf() -> None:
    package = read("brickhouse-survey-package.js")
    controller = read("analysis-package-download-v1.js")

    assert "analysis-package-download-v1.js" in package
    assert "brickhouse-survey-hybrid-pdf.js" not in package
    assert "brickhouse-survey-package-v04.js" not in package

    assert "getActiveProjectPackageInputV1" in controller
    assert "buildAnalysisPackageZipV1" in controller
    assert "const packageInput = await getPackageInput();" in controller
    assert "const built = await buildPackage({" in controller
    assert "globalThis.crypto.randomUUID()" in controller
    assert "PKG_${globalThis.crypto.randomUUID()}" in controller
    assert "appendAnalysisPackageExport" in controller
    assert "download(built.blob, built.filename)" in controller
    assert "event.stopImmediatePropagation()" in controller


def test_export_metadata_history_is_append_only_in_project_store() -> None:
    store = read("project-photo-store.js")
    assert "analysis_package_exports: []" in store
    assert "export async function appendAnalysisPackageExport" in store
    assert "Array.isArray(existing.analysis_package_exports)" in store
    assert "analysis_package_exports: [...history, { ...metadata }]" in store
    for field in (
        "agent_id",
        "agent_display_name",
        "round_id",
        "package_id",
        "filename",
        "created_at",
    ):
        assert field in store


def test_visible_copy_is_zip_on_desktop_and_phone_shell() -> None:
    html = read("photo.html")
    shell = read("photo-shell.js")
    assert ">Créer le ZIP pour Sophie</button>" in html
    assert "Le ZIP contiendra les instructions V1" in html
    assert "Ajoutez les vues puis créez le ZIP" in shell
    assert "Donnez le ZIP à Sophie, puis importez son JSON" in shell
    assert "download.textContent='Créer le ZIP pour Sophie'" in shell
    assert "actions={photos:'Créer le ZIP'" in shell
