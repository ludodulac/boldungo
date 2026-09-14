from brickhouse.scene import ArchitecturalScene, validate_scene_against_survey
from brickhouse.survey import ArchitecturalSurvey


def _survey() -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate({
        "schema_version": "0.1",
        "id": "opening_visual_survey",
        "name": "Opening visual survey",
        "photos": [{
            "photo_index": 1,
            "facade": "front",
            "description": "front",
            "source": {"kind": "user_provided", "confidence": 0.99},
            "image_left_maps_to_facade_offset": "low",
        }],
        "observations": [{
            "id": "front_window",
            "kind": "opening",
            "facade": "front",
            "certainty": "certain",
            "statement": "Window with visible stone surround, sill and shutters",
            "evidence": [{"photo_index": 1, "observation": "Surround, sill and shutters visible"}],
            "attributes": {"semantic_type": "window", "physical_object_count": 1},
            "opening_visual": {
                "frame_color": "dark_brown",
                "leaf_count": 2,
                "pane_count": 4,
                "mullion_count": 1,
                "glazing": "clear",
                "sill": "projecting",
                "surround_material": "stone_like",
                "surround_color": "light_beige",
                "surround_relief": "projecting",
                "glazing_plane": "recessed",
                "shutter_count": 2,
                "shutter_style": "folding",
                "shutter_color": "white",
            },
        }],
    })


def _scene(*, has_sill=None, has_decorative_surround=None, opening_visual=None) -> ArchitecturalScene:
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "opening_visual_scene",
        "name": "Opening visual scene",
        "units": "m",
        "volumes": [{
            "id": "main",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": {"value": 10, "source": {"kind": "inferred", "confidence": 0.7}},
            "depth": {"value": 8, "source": {"kind": "inferred", "confidence": 0.6}},
            "height": {"value": 6, "source": {"kind": "inferred", "confidence": 0.6}},
            "floors": 2,
            "source": {"kind": "inferred", "confidence": 0.6},
        }],
        "openings": [{
            "id": "front_window",
            "type": "window",
            "volume_id": "main",
            "facade": "front",
            "offset_horizontal": 2,
            "offset_vertical": 2,
            "width": 1.4,
            "height": 1.5,
            "source": {"kind": "inferred", "confidence": 0.6},
            "has_sill": has_sill,
            "has_decorative_surround": has_decorative_surround,
            "opening_visual": opening_visual,
        }],
        "appearance": {"walls": {"color": "off_white"}},
    })


def test_observed_sill_and_surround_cannot_disappear_in_scene() -> None:
    codes = {issue.code for issue in validate_scene_against_survey(_survey(), _scene())}
    assert "opening_sill_lost" in codes
    assert "opening_surround_lost" in codes


def test_observed_pane_and_shutter_composition_cannot_disappear_in_scene() -> None:
    partial = {
        "frame_color": "dark_brown",
        "leaf_count": 2,
        "mullion_count": 1,
        "glazing": "clear",
        "sill": "projecting",
        "surround_material": "stone_like",
        "surround_color": "light_beige",
    }
    issues = validate_scene_against_survey(
        _survey(),
        _scene(has_sill=True, has_decorative_surround=True, opening_visual=partial),
    )
    assert any(
        issue.code == "opening_visual_detail_lost" and "pane_count" in issue.message
        for issue in issues
    )
    assert any(
        issue.code == "opening_visual_detail_lost" and "shutter_count" in issue.message
        for issue in issues
    )


def test_qualitative_opening_planes_cannot_disappear_or_change_in_scene() -> None:
    issues = validate_scene_against_survey(
        _survey(),
        _scene(
            has_sill=True,
            has_decorative_surround=True,
            opening_visual={
                **_survey().observations[0].opening_visual.model_dump(mode="json", exclude_none=True),
                "surround_relief": "flush",
                "glazing_plane": None,
            },
        ),
    )
    assert any(
        issue.code == "opening_visual_detail_lost" and "surround_relief" in issue.message
        for issue in issues
    )
    assert any(
        issue.code == "opening_visual_detail_lost" and "glazing_plane" in issue.message
        for issue in issues
    )


def test_observed_sill_surround_composition_and_planes_are_preserved_exactly() -> None:
    visual = _survey().observations[0].opening_visual.model_dump(mode="json")
    scene = _scene(
        has_sill=True,
        has_decorative_surround=True,
        opening_visual=visual,
    )
    scene_visual = scene.openings[0].opening_visual
    assert scene_visual is not None
    assert scene_visual.surround_relief == "projecting"
    assert scene_visual.glazing_plane == "recessed"
    codes = {issue.code for issue in validate_scene_against_survey(_survey(), scene)}
    assert "opening_sill_lost" not in codes
    assert "opening_surround_lost" not in codes
    assert "opening_visual_detail_lost" not in codes


def test_none_planes_remain_none_and_do_not_create_metric_depth() -> None:
    survey = _survey()
    observation = survey.observations[0]
    visual = observation.opening_visual.model_copy(update={"surround_relief": None, "glazing_plane": None})
    survey = survey.model_copy(update={
        "observations": [observation.model_copy(update={"opening_visual": visual})]
    })
    scene = _scene(
        has_sill=True,
        has_decorative_surround=True,
        opening_visual=visual.model_dump(mode="json"),
    )
    scene_visual = scene.openings[0].opening_visual
    assert scene_visual is not None
    assert scene_visual.surround_relief is None
    assert scene_visual.glazing_plane is None
    assert not any("depth" in key for key in scene_visual.model_dump(mode="json"))
    assert "opening_visual_detail_lost" not in {
        issue.code for issue in validate_scene_against_survey(survey, scene)
    }
