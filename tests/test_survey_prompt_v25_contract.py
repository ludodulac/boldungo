from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPT = ROOT / "frontend" / "brickhouse-survey-prompt.txt"


def test_survey_v26_prompt_forbids_legacy_external_shapes() -> None:
    source = PROMPT.read_text(encoding="utf-8")
    assert "BRICKHOUSE — PROMPT DE RELEVÉ ARCHITECTURAL v2.9" in source
    assert '"front_facade":"front"' in source
    assert '"x_direction":"front_view_left_to_right"' in source
    assert '"y_direction":"front_to_rear"' in source
    assert '"z_direction":"bottom_to_top"' in source
    assert 'source` = `{ "kind":"user_provided|observed|inferred|generated_default", "confidence":0..1 }`' in source
    assert 'Chaque `evidence[]` = `{ "photo_index":1, "observation":"..." }`' in source
    assert "N’invente AUCUN alias de champ" in source
    assert "N’ajoute jamais de racine `physical_objects`" in source
    assert "N’utilise jamais les anciens champs `x`, `y`, `z`, `orientation_source`" in source
    assert "N’utilise jamais une chaîne telle que `\"photo_1\"` comme élément d’evidence" in source


def test_survey_v26_prompt_requires_roof_and_exterior_multiview_audits() -> None:
    source = PROMPT.read_text(encoding="utf-8")
    assert "DÉCOMPOSITION PALIER / VOLUME PORTEUR / TERRASSE — AUDIT MULTI-VUES" in source
    assert "TOITURE — CERTITUDE OBJET VS ATTRIBUTS" in source
    assert 'attributes.facade_is_gable:true' in source
    assert 'attribute_certainty.facade_is_gable' in source
    assert 'attributes.roof_type' in source
    assert 'attribute_certainty.roof_type' in source
    assert "certitude de toiture séparée de ses attributs" in source
