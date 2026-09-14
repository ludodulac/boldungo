import json
from pathlib import Path

from brickhouse.building import OpeningVisualDescription as BuildingOpeningVisualDescription
from brickhouse.survey import ArchitecturalSurvey
from brickhouse.survey import OpeningVisualDescription as SurveyOpeningVisualDescription
from brickhouse.survey.models import SurveyObservation


def test_survey_and_building_share_the_same_opening_visual_class():
    assert SurveyOpeningVisualDescription is BuildingOpeningVisualDescription
    annotation = SurveyObservation.model_fields["opening_visual"].annotation
    assert BuildingOpeningVisualDescription in annotation.__args__


def test_existing_real_house_survey_fixture_still_validates():
    payload = json.loads(
        Path("frontend/benchmarks/real-house-5/accepted-survey-v0.1.json").read_text(encoding="utf-8")
    )
    survey = ArchitecturalSurvey.model_validate(payload)
    assert survey.id == payload["id"]
    assert len(survey.observations) == len(payload["observations"])


def test_historical_json_shape_roundtrips_without_new_explicit_fields():
    payload = {
        "frame_color": "brown",
        "pane_count": 2,
        "glazing": "glazed",
        "sill": "stone",
        "surround_color": "beige",
        "shutter_count": 2,
        "notes": "observed",
    }
    visual = SurveyOpeningVisualDescription.model_validate(payload)
    assert visual.model_dump(mode="json", exclude_unset=True) == payload


def test_roundtrip_is_deterministic_and_preserves_explicit_nulls():
    payload = {"surround_color": "beige", "sill_color": None}
    first = SurveyOpeningVisualDescription.model_validate(payload)
    encoded = first.model_dump(mode="json", exclude_unset=True)
    second = SurveyOpeningVisualDescription.model_validate(encoded)
    assert encoded == payload
    assert second.model_dump(mode="json", exclude_unset=True) == payload
