import json
from pathlib import Path

from brickhouse.scene import validate_scene_against_survey
from brickhouse.scene.benchmark_scene_recipe import (
    _merge_explicit_survey_opening_visual,
    materialize_scene_recipe,
)
from brickhouse.survey import ArchitecturalSurvey


ROOT = Path(__file__).resolve().parents[2]
BENCHMARK = ROOT / "frontend" / "benchmarks" / "real-house-5"
RECIPE = BENCHMARK / "scene-candidate-v0.2.json"
SURVEY = BENCHMARK / "accepted-survey-v0.1.json"
FRONT_CHARACTERISTIC_OPENINGS = (
    "front-opening-1",
    "front-opening-2",
    "front-opening-3",
    "front-opening-4",
)
RESTORED_COMPOSITION = {
    "leaf_count": 2,
    "mullion_count": 1,
    "glazing": "dark_reflective",
    "frame_color": "dark_gray_brown",
    "frame_material": "painted_or_dark_joinery",
    "surround_color": "beige",
    "surround_relief": "projecting",
    "glazing_plane": "recessed",
}


def test_generic_merge_preserves_explicit_visuals_without_erasing_with_none() -> None:
    payload = {
        "openings": [
            {
                "id": "window-1",
                "opening_visual": {
                    "surround_color": "beige",
                    "glazing": "clear",
                },
            },
            {
                "id": "window-2",
                "opening_visual": {"surround_color": "grey"},
            },
        ]
    }
    survey = {
        "observations": [
            {
                "id": "window-1",
                "kind": "opening",
                "opening_visual": {
                    "surround_relief": "projecting",
                    "glazing_plane": "recessed",
                    "surround_color": None,
                },
            },
            {
                "id": "window-2",
                "kind": "opening",
                "opening_visual": None,
            },
        ]
    }

    _merge_explicit_survey_opening_visual(payload, survey)

    first = payload["openings"][0]["opening_visual"]
    assert first == {
        "surround_color": "beige",
        "glazing": "clear",
        "surround_relief": "projecting",
        "glazing_plane": "recessed",
    }
    assert payload["openings"][1]["opening_visual"] == {"surround_color": "grey"}


def test_real_house_accepted_survey_retains_acquired_front_window_composition() -> None:
    survey = ArchitecturalSurvey.model_validate(json.loads(SURVEY.read_text(encoding="utf-8")))
    observations = {observation.id: observation for observation in survey.observations}

    for opening_id in FRONT_CHARACTERISTIC_OPENINGS:
        visual = observations[opening_id].opening_visual
        assert visual is not None
        for field, expected in RESTORED_COMPOSITION.items():
            assert getattr(visual, field) == expected
        # Historical evidence established two leaves separated by a central mullion.
        # It did not canonically establish that those two observed parts are panes.
        assert visual.pane_count is None
        assert visual.pane_layout is None


def test_real_house_materialization_preserves_p1_opening_planes_and_existing_visuals() -> None:
    scene = materialize_scene_recipe(RECIPE)
    openings = {opening.id: opening for opening in scene.openings}

    for opening_id in FRONT_CHARACTERISTIC_OPENINGS:
        visual = openings[opening_id].opening_visual
        assert visual is not None
        for field, expected in RESTORED_COMPOSITION.items():
            assert getattr(visual, field) == expected
        assert visual.pane_count is None
        assert visual.pane_layout is None

    # Survey None remains unresolved: existing Scene semantics survive, but the
    # restored composition and qualitative planes are not invented elsewhere.
    assert openings["front-opening-5"].opening_visual.surround_color == "beige"
    assert openings["front-opening-5"].opening_visual.surround_relief is None
    assert openings["front-opening-5"].opening_visual.glazing_plane is None
    assert openings["front-opening-5"].opening_visual.leaf_count is None
    assert openings["front-opening-5"].opening_visual.mullion_count is None
    assert openings["front-opening-6"].opening_visual.glazing == "glazed"
    assert openings["front-opening-6"].opening_visual.surround_relief is None
    assert openings["front-opening-6"].opening_visual.glazing_plane is None
    assert openings["front-opening-6"].opening_visual.leaf_count is None
    assert openings["front-opening-6"].opening_visual.mullion_count is None


def test_real_house_opening_visual_fidelity_accepts_materialized_scene() -> None:
    survey = ArchitecturalSurvey.model_validate(json.loads(SURVEY.read_text(encoding="utf-8")))
    scene = materialize_scene_recipe(RECIPE)
    issues = validate_scene_against_survey(survey, scene)

    target_ids = set(FRONT_CHARACTERISTIC_OPENINGS)
    assert not [
        issue
        for issue in issues
        if issue.code == "opening_visual_detail_lost" and issue.object_id in target_ids
    ]
