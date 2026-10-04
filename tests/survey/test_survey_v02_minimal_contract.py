from pathlib import Path
from brickhouse.survey import ArchitecturalSurvey, KnowledgeMode, StructureRole, validate_survey_semantics

def test_survey_01_remains_readable_without_invented_knowledge_mode():
    survey = ArchitecturalSurvey.model_validate({
        "schema_version":"0.1","id":"legacy","name":"legacy",
        "photos":[{"photo_index":1,"facade":"front","description":"front","source":{"kind":"observed","confidence":1},"image_left_maps_to_facade_offset":"low"}],
        "observations":[{"id":"roof","kind":"roof","certainty":"certain","statement":"roof exists","evidence":[{"photo_index":1,"observation":"visible"}]}],
    })
    assert survey.observations[0].knowledge_mode is None

def test_knowledge_mode_is_independent_from_certainty_and_properties():
    survey = ArchitecturalSurvey.model_validate({
        "schema_version":"0.2","id":"epistemic","name":"epistemic",
        "photos":[{"photo_index":1,"facade":"front","description":"front","source":{"kind":"observed","confidence":1},"image_left_maps_to_facade_offset":"low"}],
        "observations":[{"id":"roof","kind":"roof","certainty":"certain","knowledge_mode":"deduced_multiview","statement":"gable roof","evidence":[{"photo_index":1,"observation":"gable"}],"attributes":{"roof_type":"gable"},"attribute_certainty":{"roof_type":"certain"},"attribute_knowledge_mode":{"roof_type":"deduced_multiview"}}],
    })
    assert survey.observations[0].knowledge_mode is KnowledgeMode.DEDUCED_MULTIVIEW
    assert survey.observations[0].certainty.value == "certain"

def test_structure_can_exist_without_count_or_coordinates():
    survey = ArchitecturalSurvey.model_validate({
        "schema_version":"0.2","id":"structure","name":"structure",
        "photos":[{"photo_index":1,"facade":"front","description":"front","source":{"kind":"observed","confidence":1},"image_left_maps_to_facade_offset":"low"}],
        "observations":[{"id":"post","kind":"structure","structure_role":"vertical_support","certainty":"certain","knowledge_mode":"observed","statement":"post visible","evidence":[{"photo_index":1,"observation":"post"}]}],
    })
    assert survey.observations[0].structure_role is StructureRole.VERTICAL_SUPPORT

def test_real_house_five_photo_survey02_candidate_is_semantically_valid():
    path=Path("frontend/benchmarks/real-house-5/five-photo-survey-candidate-v0.1.json")
    survey=ArchitecturalSurvey.model_validate_json(path.read_text())
    assert survey.schema_version == "0.2"
    relation=next(item for item in survey.relations if item.id=="relation-deck-landing-hypothesis")
    assert relation.knowledge_mode is KnowledgeMode.HYPOTHESIS
    assert relation.certainty.value == "plausible"
    assert validate_survey_semantics(survey) == []
