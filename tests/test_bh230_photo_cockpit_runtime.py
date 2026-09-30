from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PHOTO_HTML = ROOT / "frontend" / "photo.html"
CAPTURE = ROOT / "frontend" / "photo-capture-runtime.js"
PACKAGE = ROOT / "frontend" / "brickhouse-survey-package.js"


def test_normal_photo_cockpit_uses_capture_only_runtime() -> None:
    html = PHOTO_HTML.read_text(encoding="utf-8")
    assert "photo-capture-runtime.js?v=photo-capture-1.0" in html
    assert '<script type="module" src="./photo.js"></script>' not in html
    assert '<script type="module" src="./photo-simple.js' not in html
    assert 'id="photo-persistence-note"' in html
    assert "conservées localement dans ce navigateur sur cet appareil" in html
    assert "effacez les données du navigateur ou changez d’appareil" in html
    assert 'value="https://brickhouse-api.onrender.com"' in html


def test_capture_runtime_does_not_own_analysis_or_package_actions() -> None:
    source = CAPTURE.read_text(encoding="utf-8")
    assert "#download-ai-package" not in source
    assert "#import-analysis" not in source
    assert "fetch(" not in source
    assert "#guided-photo-grid" in source
    assert "DataTransfer" in source
    assert "project-photo-store.js" in source
    assert "indexedDB" not in source


def test_current_pdf_and_benchmark_paths_remain_active() -> None:
    package = PACKAGE.read_text(encoding="utf-8")
    assert "brickhouse-survey-hybrid-pdf.js?v=pdf-handoff-0.10-hybrid-text" in package
    assert "real-house-benchmark-loader.js?v=real-house-5-preload-0.2-scene-checkpoint" in package
    assert "photo-slot-previews.js?v=photo-slot-previews-0.1" in package


def test_historical_runtimes_are_preserved_in_repository() -> None:
    assert (ROOT / "frontend" / "photo.js").exists()
    assert (ROOT / "frontend" / "photo-simple.js").exists()
    assert (ROOT / "frontend" / "brickhouse-survey-package-v04.js").exists()
    assert (ROOT / "frontend" / "brickhouse-survey-package-v14.js").exists()
