from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def implementation_source() -> str:
    return (FRONTEND / "brickhouse-survey-package-v04.js").read_text(encoding="utf-8")


def test_external_import_loads_survey_first_pdf_override() -> None:
    importer = (FRONTEND / "external-bundle-import.js").read_text(encoding="utf-8")
    assert "import './brickhouse-survey-package.js';" in importer


def test_stable_entry_point_loads_zip_v1_and_not_legacy_pdf_runtime() -> None:
    loader = (FRONTEND / "brickhouse-survey-package.js").read_text(encoding="utf-8")
    assert "analysis-package-download-v1.js?v=exchange-v1-sophie-r001" in loader
    assert "brickhouse-survey-package-v04.js?v=pdf-handoff-0.4" not in loader
    assert "brickhouse-survey-hybrid-pdf.js" not in loader


def test_initial_pdf_requests_only_architectural_survey() -> None:
    source = implementation_source()
    assert "PDF_HANDOFF_VERSION = 'pdf-handoff-0.4'" in source
    assert "brickhouse-survey-result.json" in source
    assert "produis UNIQUEMENT un ArchitecturalSurvey v0.1 complet" in source
    assert "NE CONSTRUIS PAS DE SCENE dans ce tour" in source
    assert '{\\"ArchitecturalSurvey\\":{...}}' in source
    assert '{\\"survey\\":{...}}' in source
    assert "Scene ou autre wrapper" in source
    assert "brickhouse-survey-to-scene-prompt.txt" not in source


def test_survey_first_pdf_audits_facade_and_targeted_detail_photos_separately() -> None:
    source = implementation_source()
    assert "id et name sont présents et non vides" in source
    assert "capture_role=facade_view" in source
    assert "image_left_maps_to_facade_offset vaut low|high" in source
    assert "capture_role=targeted_detail" in source
    assert "facade=null" in source
    assert "image_left_maps_to_facade_offset=null" in source
    assert "ne fabrique jamais une façade" in source
    assert 'semantic_type:\\"opening\\"' in source
    assert "chaque relation référence deux IDs d’observations existantes" in source


def test_survey_first_pdf_keeps_topology_as_intermediate_reasoning() -> None:
    source = implementation_source()
    assert "brickhouse-topology-prompt.txt" in source
    assert "brickhouse-survey-prompt.txt" in source
    assert "TOPOLOGIE — RAISONNEMENT INTERMÉDIAIRE" in source
    assert "ARCHITECTURAL SURVEY — CONTRAT AUTORITATIF" in source


def test_mobile_pdf_encodes_and_releases_each_canvas_before_next_page() -> None:
    source = implementation_source()
    assert "encodeCanvasPage" in source
    assert "releaseCanvas" in source
    assert "canvas.width = 1" in source
    assert "pdfFromImages" in source
    assert "pdfFromCanvases" not in source
    assert "assertCanvasHealthy" in source
    assert "getImageData" in source
    assert "PDF NON téléchargé" in source


def test_mobile_pdf_uses_unambiguous_versioned_filename() -> None:
    source = implementation_source()
    assert "PACKAGE_FILENAME = 'BRICKHOUSE-SURVEY-pdf-handoff-0.4.pdf'" in source
    assert "contrôle anti-pages-noires actif" in source
