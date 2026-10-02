from pathlib import Path


TOPOLOGY_AUDIT = Path("frontend/brickhouse-survey-topology-audit-v30.txt")
PACKAGE_ENTRY = Path("frontend/brickhouse-survey-package.js")
PACKAGE_WRAPPER = Path("frontend/brickhouse-survey-package-v06.js")


def test_topology_addendum_requires_building_boundary_anchor():
    text = TOPOLOGY_AUDIT.read_text(encoding="utf-8")
    assert "ADDENDUM PHOTOS → SURVEY v3.0 — COMPLÉTUDE TOPOLOGIQUE" in text
    assert "ENVELOPPE DU BÂTIMENT — ANCRE TOPOLOGIQUE OBLIGATOIRE" in text
    assert 'kind:"building_boundary"' in text
    assert "Ne l'omets pas" in text
    assert "NON MÉTRIQUE" in text


def test_topology_addendum_requires_proven_external_connections():
    text = TOPOLOGY_AUDIT.read_text(encoding="utf-8")
    assert "AUDIT DES RACCORDEMENTS — OBLIGATOIRE AVANT SORTIE" in text
    assert 'kind:"platform"' in text
    assert 'kind:"stair"' in text
    assert "relation `connects_to` certaine" in text
    assert "Une relation de support (`supports`) ne remplace jamais" in text
    assert "PRÉFLIGHT DE COMPLÉTUDE" in text
    assert "aucune métrique n'est inventée" in text


def test_zip_v1_handoff_preserves_topology_after_terrain_without_legacy_pdf_runtime():
    entry = PACKAGE_ENTRY.read_text(encoding="utf-8")
    wrapper = PACKAGE_WRAPPER.read_text(encoding="utf-8")
    assert "analysis-package-download-v1.js" in entry
    assert "brickhouse-survey-package-v04.js" not in entry
    assert "brickhouse-survey-hybrid-pdf.js" not in entry
    assert "brickhouse-survey-package-v05.js" in entry
    assert "pdf-handoff-0.5-terrain-audit" in entry
    assert "brickhouse-survey-package-v06.js" in entry
    assert "pdf-handoff-0.6-topology-audit" in entry
    assert entry.index("brickhouse-survey-package-v05.js") < entry.index("brickhouse-survey-package-v06.js")
    assert "brickhouse-survey-package-v05.js" in wrapper
    assert "brickhouse-survey-topology-audit-v30.txt" in wrapper
    assert "brickhouse-survey-prompt.txt" in wrapper
    assert "`${promptWithTerrainAudit}\\n\\n${topologyAudit}`" in wrapper
