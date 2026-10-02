from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "frontend" / "brickhouse-survey-package.js"
HYBRID = ROOT / "frontend" / "brickhouse-survey-hybrid-pdf.js"


def test_hybrid_pdf_is_historical_and_not_registered_in_normal_zip_v1_runtime():
    entry = ENTRY.read_text(encoding="utf-8")
    assert "./analysis-package-download-v1.js?v=exchange-v1-sophie-r001" in entry
    assert "./brickhouse-survey-hybrid-pdf.js?v=pdf-handoff-0.10-hybrid-text" not in entry
    assert "./brickhouse-survey-package-v04.js?v=pdf-handoff-0.4" not in entry
    assert HYBRID.exists()


def test_historical_hybrid_pdf_emits_native_text_and_jpeg_photo_pages():
    source = HYBRID.read_text(encoding="utf-8")
    assert "pdf-handoff-0.10-hybrid-text" in source
    assert "BRICKHOUSE-SURVEY-pdf-handoff-0.10.pdf" in source
    assert "makeTextPages" in source
    assert "kind: 'text'" in source
    assert "/Subtype /Type1 /BaseFont /Helvetica" in source
    assert " Tj\\n" in source
    assert "/Font << /F1" in source
    assert "makePhotoPage" in source
    assert "kind: 'image'" in source
    assert "/Subtype /Image" in source
    assert "/Filter /DCTDecode" in source


def test_historical_hybrid_pdf_keeps_capture_contract_for_compatibility():
    source = HYBRID.read_text(encoding="utf-8")
    assert "fetchText('./brickhouse-topology-prompt.txt')" in source
    assert "fetchText('./brickhouse-survey-prompt.txt')" in source
    assert "fetchText('./brickhouse-survey-output-contract.txt')" in source
    assert "capture_role=${record.captureRole}" in source
    assert "orientation_authority=${record.orientationAuthority}" in source
    assert "largeur réelle de façade avant" in source
    assert "brickhouse-survey-result.json" in source
    assert "event.stopImmediatePropagation()" in source
