from pathlib import Path

AUDIT = Path("frontend/brickhouse-survey-multiview-identity-audit-v39.txt")
PACKAGE = Path("frontend/brickhouse-survey-package-v14.js")
ENTRY = Path("frontend/brickhouse-survey-package.js")


def test_multiview_identity_audit_requires_explicit_correspondence_before_fusion():
    text = AUDIT.read_text(encoding="utf-8")

    assert "attributes.multiview_identity" in text
    assert '"same_physical_object"' in text
    assert '"unresolved"' in text
    assert "shape_detail" in text
    assert "relative_position" in text
    assert "supporting_relation_ids" in text
    assert "ne fusionne pas immédiatement" in text


def test_multiview_identity_audit_rejects_similarity_and_projection_as_proof():
    text = AUDIT.read_text(encoding="utf-8")

    assert "ressemblance générique" in text
    assert "projection 2D" in text
    assert "ne prouve PAS" in text


def test_multiview_identity_audit_separates_architectural_identity_topology_and_geometry():
    text = AUDIT.read_text(encoding="utf-8")

    assert "plusieurs volées/`StairRun`" in text
    assert "`connects_to`" in text
    assert "`adjacent_to`" in text
    assert "`part_of`" in text
    assert "ne deviennent jamais `same_physical_object`" in text
    assert "n’est transitive par défaut" in text
    assert "géométrie `unresolved`" in text
    assert "espace couvert OUVERT" in text
    assert "ne doit jamais être fermé" in text


def test_v14_package_is_layered_after_ownership_and_active():
    package = PACKAGE.read_text(encoding="utf-8")
    entry = ENTRY.read_text(encoding="utf-8")

    assert "brickhouse-survey-package-v13.js" in package
    assert "brickhouse-survey-multiview-identity-audit-v39.txt" in package
    assert "multiviewIdentityAwareSurveyFetch" in package
    assert "brickhouse-survey-package-v14.js" in entry
