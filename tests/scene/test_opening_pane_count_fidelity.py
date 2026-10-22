import json
from copy import deepcopy
from pathlib import Path

from brickhouse.bricks.architectural_solutions import rank_window_solutions
from brickhouse.scene import (
    ArchitecturalScene,
    project_scene_to_building,
    validate_scene_against_survey,
)
from brickhouse.survey import ArchitecturalSurvey


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "generic_opening_pane_count_fidelity.json"
FRONTEND = ROOT / "frontend"


def _fixture():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    survey = ArchitecturalSurvey.model_validate(payload["survey"])
    scene = ArchitecturalScene.model_validate(payload["scene"])
    return survey, scene


def test_active_photo_survey_prompt_defines_panes_without_inventing_leaves_or_style() -> None:
    loader = (FRONTEND / "brickhouse-survey-package.js").read_text(encoding="utf-8")
    wrapper = (FRONTEND / "brickhouse-survey-package-v15.js").read_text(encoding="utf-8")
    audit = (FRONTEND / "brickhouse-survey-opening-pane-audit-v40.txt").read_text(encoding="utf-8")

    assert "brickhouse-survey-package-v15.js?v=pdf-handoff-0.15-opening-pane-semantics" in loader
    assert "brickhouse-survey-opening-pane-audit-v40.txt" in wrapper
    assert "nombre de subdivisions / zones vitrées visuellement distinctes et observables" in audit
    assert "Ne déduis JAMAIS `leaf_count` de `pane_count`" in audit
    assert "de style `PAIRED`" in audit


def test_two_observed_panes_survive_survey_scene_projection_without_leaf_or_style_invention() -> None:
    survey, scene = _fixture()
    survey_opening = next(item for item in survey.observations if item.id == "window_two_visible_panes")
    scene_opening = next(item for item in scene.openings if item.id == "window_two_visible_panes")

    assert survey_opening.opening_visual is not None
    assert survey_opening.opening_visual.pane_count == 2
    assert survey_opening.opening_visual.leaf_count is None
    assert survey_opening.opening_visual.pane_layout is None

    assert scene_opening.opening_visual is not None
    assert scene_opening.opening_visual.pane_count == 2
    assert scene_opening.opening_visual.leaf_count is None
    assert scene_opening.window_style is None

    fidelity_issues = validate_scene_against_survey(survey, scene)
    assert not any(issue.code == "opening_visual_detail_lost" for issue in fidelity_issues)

    projection = project_scene_to_building(scene)
    assert not projection.blocked
    assert projection.building is not None
    building_opening = next(item for item in projection.building.openings if item.id == "window_two_visible_panes")
    assert building_opening.opening_visual is not None
    assert building_opening.opening_visual.pane_count == 2
    assert building_opening.opening_visual.leaf_count is None
    assert building_opening.window_style is None


def test_existing_planner_can_choose_paired_representation_without_mutating_architectural_leaf_semantics() -> None:
    _, scene = _fixture()
    projection = project_scene_to_building(scene)
    assert projection.building is not None
    opening = next(item for item in projection.building.openings if item.id == "window_two_visible_panes")
    before = deepcopy(opening.model_dump())

    selection = rank_window_solutions(
        architectural_width_m=opening.width,
        architectural_height_m=opening.height,
        raster_width_studs=4,
        raster_height_bricks=3,
        observed_leaf_count=opening.opening_visual.leaf_count,
        observed_pane_count=opening.opening_visual.pane_count,
    )

    assert selection.recommended is not None
    assert selection.recommended.composition == "paired"
    assert opening.model_dump() == before
    assert opening.opening_visual.leaf_count is None
    assert opening.window_style is None


def test_unknown_topology_stays_unknown_and_planner_does_not_require_invented_subdivisions() -> None:
    survey, scene = _fixture()
    survey_opening = next(item for item in survey.observations if item.id == "window_unknown_topology")
    scene_opening = next(item for item in scene.openings if item.id == "window_unknown_topology")

    assert survey_opening.opening_visual is not None
    assert survey_opening.opening_visual.pane_count is None
    assert survey_opening.opening_visual.leaf_count is None
    assert survey_opening.opening_visual.pane_layout is None
    assert scene_opening.opening_visual is not None
    assert scene_opening.opening_visual.pane_count is None
    assert scene_opening.opening_visual.leaf_count is None
    assert scene_opening.window_style is None

    projection = project_scene_to_building(scene)
    assert projection.building is not None
    opening = next(item for item in projection.building.openings if item.id == "window_unknown_topology")
    before = deepcopy(opening.model_dump())
    selection = rank_window_solutions(
        architectural_width_m=opening.width,
        architectural_height_m=opening.height,
        raster_width_studs=2,
        raster_height_bricks=3,
        observed_leaf_count=None,
        observed_pane_count=None,
    )

    assert selection.recommended is not None
    assert selection.recommended.composition == "single"
    assert opening.model_dump() == before
    assert opening.opening_visual.leaf_count is None
    assert opening.opening_visual.pane_count is None
    assert opening.window_style is None
