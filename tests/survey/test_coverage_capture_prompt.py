from pathlib import Path


COVERAGE_AUDIT = Path("frontend/brickhouse-survey-coverage-audit-v31.txt")
PACKAGE_ENTRY = Path("frontend/brickhouse-survey-package.js")
PACKAGE_WRAPPER = Path("frontend/brickhouse-survey-package-v07.js")


def test_coverage_addendum_closes_visible_roof_inventory():
    text = COVERAGE_AUDIT.read_text(encoding="utf-8")
    assert "ADDENDUM PHOTOS → SURVEY v3.1 — FERMETURE DE COUVERTURE" in text
    assert "TOITURE — PRÉSENCE AVANT FORME" in text
    assert 'observation `kind:"roof"`' in text
    assert "PRÉFLIGHT TOITURE MULTI-VUES" in text
    assert "Ne supprime jamais l'observation de toiture" in text
    assert "N'invente aucune métrique" in text


def test_coverage_addendum_rechecks_boundary_and_exact_root_contract():
    text = COVERAGE_AUDIT.read_text(encoding="utf-8")
    assert 'kind:"building_boundary"' in text
    assert "La racine finale doit utiliser exactement `id`, jamais `survey_id`" in text
    assert "PRÉFLIGHT FINAL — OBLIGATOIRE AVANT JSON" in text
    assert "aucune métrique, façade, relation, direction ou forme n'est inventée" in text


def test_zip_v1_handoff_preserves_coverage_after_topology_without_legacy_pdf_runtime():
    entry = PACKAGE_ENTRY.read_text(encoding="utf-8")
    wrapper = PACKAGE_WRAPPER.read_text(encoding="utf-8")
    assert "analysis-package-download-v1.js" in entry
    assert "brickhouse-survey-package-v04.js" not in entry
    assert "brickhouse-survey-hybrid-pdf.js" not in entry
    assert "brickhouse-survey-package-v05.js" in entry
    assert "brickhouse-survey-package-v06.js" in entry
    assert "brickhouse-survey-package-v07.js" in entry
    assert "pdf-handoff-0.7-coverage-audit" in entry
    assert entry.index("brickhouse-survey-package-v05.js") < entry.index("brickhouse-survey-package-v06.js") < entry.index("brickhouse-survey-package-v07.js")
    assert "brickhouse-survey-package-v06.js" in wrapper
    assert "brickhouse-survey-coverage-audit-v31.txt" in wrapper
    assert "brickhouse-survey-prompt.txt" in wrapper
    assert "`${promptWithTopologyAudit}\\n\\n${coverageAudit}`" in wrapper
