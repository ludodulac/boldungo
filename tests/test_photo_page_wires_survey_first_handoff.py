from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def test_photo_page_loads_survey_first_handoff_instead_of_legacy_bundle_handoff() -> None:
    html = (FRONTEND / "photo.html").read_text(encoding="utf-8")
    assert 'src="./brickhouse-survey-package.js?v=photo-cockpit-1.0"' in html
    assert 'src="./brickhouse-single-package.js"' not in html


def test_stable_handoff_entry_point_uses_zip_v1_and_preserves_audit_layers() -> None:
    loader = (FRONTEND / "brickhouse-survey-package.js").read_text(encoding="utf-8")
    implementation = (FRONTEND / "brickhouse-survey-package-v04.js").read_text(encoding="utf-8")
    assert "analysis-package-download-v1.js?v=exchange-v1-sophie-r001" in loader
    assert "brickhouse-survey-package-v04.js?v=pdf-handoff-0.4" not in loader
    assert "brickhouse-survey-package-v07.js?v=pdf-handoff-0.7-coverage-audit" in loader
    assert "brickhouse-survey-package-v08.js?v=pdf-handoff-0.8-final-contract-audit" in loader
    assert "brickhouse-survey-package-v11.js?v=pdf-handoff-0.11-orientation-provenance" in loader
    assert "brickhouse-survey-hybrid-pdf.js?v=pdf-handoff-0.10-hybrid-text" not in loader
    assert "pdf-handoff-0.4" in implementation
    assert "brickhouse-survey-result.json" in implementation
