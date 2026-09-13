from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENE_PROMPT = ROOT / "frontend" / "brickhouse-survey-to-scene-prompt.txt"
SURVEY_PROMPT = ROOT / "frontend" / "brickhouse-survey-prompt.txt"
TOPOLOGY_PROMPT = ROOT / "frontend" / "brickhouse-topology-prompt.txt"


def test_scene_prompt_forbids_unconstrained_metric_completion() -> None:
    source = SCENE_PROMPT.read_text(encoding="utf-8")
    assert "ouverture Scene ne peut intersecter un span `occluded` ou `unknown`" in source
    assert "start.x == end.x` OU `start.y == end.y" in source
    assert "tolérance 0,12 m" in source
    assert "chaque Platform rendue touche un volume suffisamment défini ou une StairRun" in source
    assert "connexion cachée inventée pour satisfaire le validateur" in source
    assert 'geometry_status:"unresolved"' in source
    assert "Ne déplace pas l’extrémité jusqu’à l’objet pour fabriquer le contact" in source


def test_survey_prompt_is_locked_to_backend_v01_shapes() -> None:
    source = SURVEY_PROMPT.read_text(encoding="utf-8")
    assert "RELEVÉ ARCHITECTURAL v2.9" in source
    assert 'schema_version` DOIT valoir exactement `"0.1"' in source
    assert '"kind":"front_width"' in source
    assert "subject_id" in source
    assert "object_id" in source
    assert "same_physical_object" in source
    assert "TOITURE — CERTITUDE OBJET VS ATTRIBUTS" in source
    assert "attributes.semantic_type" in source
    assert "attribute_certainty" in source
    assert "SupportPost" in SCENE_PROMPT.read_text(encoding="utf-8")
    assert "n’est PAS une deuxième observation `kind=\"platform\"`" in source


def test_topology_prompt_obeys_single_turn_and_has_conditional_orientation_authority() -> None:
    source = TOPOLOGY_PROMPT.read_text(encoding="utf-8")
    assert "TOPOLOGIQUE v0.8" in source
    assert "execution_mode=single_turn_file_output" in source
    assert "N’ENTRE PAS en mode conversationnel" in source
    assert "slot_labels_are_user_confirmed" in source
