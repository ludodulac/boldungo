from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMPORTER = ROOT / "frontend" / "external-bundle-import.js"
SURVEY_MODEL = ROOT / "backend" / "brickhouse" / "survey" / "models.py"
SCENE_MODEL = ROOT / "backend" / "brickhouse" / "scene" / "models.py"


def test_external_bundle_importer_rejects_nested_schema_drift_explicitly() -> None:
    source = IMPORTER.read_text(encoding="utf-8")
    assert "function isBundleRoot" in source
    assert "function looksLikeBundle" in source
    assert "function bundleContractIssue" in source
    assert "Version de l’enveloppe incompatible" in source
    assert "Type d’enveloppe incompatible" in source
    assert "Version Survey incompatible" in source
    assert "Version Scene incompatible" in source
    assert "event.stopImmediatePropagation()" in source
    assert "Régénérez le résultat avec la commande BrickHouse la plus récente" in source
    assert "Survey invalide :" in source


def test_prompt_contract_versions_match_backend_literals() -> None:
    survey_model = SURVEY_MODEL.read_text(encoding="utf-8")
    scene_model = SCENE_MODEL.read_text(encoding="utf-8")
    survey_prompt = (ROOT / "frontend" / "brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    scene_prompt = (ROOT / "frontend" / "brickhouse-survey-to-scene-prompt.txt").read_text(encoding="utf-8")

    assert 'schema_version: Literal["0.1", "0.2"]' in survey_model
    assert 'schema_version: Literal["0.2"]' in scene_model
    assert 'exactement `"0.1"' in survey_prompt
    assert 'exactement `"0.2"' in scene_prompt


def test_scene_prompt_tracks_backend_coordinate_and_opening_shapes() -> None:
    model = SCENE_MODEL.read_text(encoding="utf-8")
    prompt = (ROOT / "frontend" / "brickhouse-survey-to-scene-prompt.txt").read_text(encoding="utf-8")

    assert "class SceneVolume" in model
    assert "class SceneOpening" in model
    assert "class SupportPost" in model
    assert "Position3D est TOUJOURS un objet" in prompt
    assert 'type":"window|door|garage_door' in prompt
    assert "SupportPost" in prompt
    assert "Ne représente jamais un poteau/support par une deuxième Platform" in prompt
