import json
from pathlib import Path

from brickhouse.scene.benchmark_scene_recipe import materialize_scene_recipe


ROOT = Path(__file__).resolve().parents[2]
BENCHMARK = ROOT / "frontend" / "benchmarks" / "real-house-5"
RECIPE = BENCHMARK / "scene-candidate-v0.2.json"
BASE_SCENE = ROOT / "tests" / "fixtures" / "real_house_5_scene_candidate.json"
ACCEPTED_SURVEY = BENCHMARK / "accepted-survey-v0.1.json"
OVERLAY = BENCHMARK / "right-facade-grade-opening-scene-overlay-v0.1.json"

GLASS_BLOCK_OPENING_ID = "right-opening-3"
SIDEWALK_CONTACT_OPENING_ID = "right-opening-2"
RECT_FIELDS = ("offset_horizontal", "offset_vertical", "width", "height")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _opening(scene, opening_id: str):
    return next(item for item in scene.openings if item.id == opening_id)


def test_right_facade_mapping_is_documented_from_p2_evidence() -> None:
    survey = _load(ACCEPTED_SURVEY)
    overlay = _load(OVERLAY)
    observations = {item["id"]: item for item in survey["observations"]}

    assert "Petite ouverture basse proche de l'angle avant" in observations[SIDEWALK_CONTACT_OPENING_ID]["statement"]
    assert "blocs translucides" in observations[GLASS_BLOCK_OPENING_ID]["statement"]

    mapping = overlay["mapping"]
    assert mapping["glass_block_opening_id"] == GLASS_BLOCK_OPENING_ID
    assert mapping["sidewalk_contact_opening_id"] == SIDEWALK_CONTACT_OPENING_ID
    assert mapping["same_opening"] is False


def test_glass_blocks_are_explicit_without_changing_architectural_type() -> None:
    scene = materialize_scene_recipe(RECIPE)
    opening = _opening(scene, GLASS_BLOCK_OPENING_ID)

    assert opening.type.value == "unknown"
    assert opening.opening_visual is not None
    assert opening.opening_visual.glazing == "glass_block"
    assert opening.opening_visual.pane_layout == "square_grid"
    assert opening.opening_visual.pane_count is None


def test_sidewalk_contact_is_zero_local_grade_clearance() -> None:
    scene = materialize_scene_recipe(RECIPE)
    opening = _opening(scene, SIDEWALK_CONTACT_OPENING_ID)

    assert opening.local_grade_clearance == 0
    assert any(
        "WALL_DATUM" in evidence.observation
        and "TERRAIN_DATUM" in evidence.observation
        for evidence in opening.evidence
    )


def test_all_right_opening_rectangles_are_exactly_unchanged() -> None:
    base = _load(BASE_SCENE)
    scene = materialize_scene_recipe(RECIPE)

    before = {
        item["id"]: tuple(item[field] for field in RECT_FIELDS)
        for item in base["openings"]
        if item["facade"] == "right"
    }
    after = {
        item.id: tuple(getattr(item, field) for field in RECT_FIELDS)
        for item in scene.openings
        if item.facade.value == "right"
    }

    assert before == {
        "right-opening-1": (2.3, 4.75, 1.15, 1.65),
        "right-opening-2": (1.0, 0.55, 0.55, 0.6),
        "right-opening-3": (6.3, 0.55, 1.0, 0.85),
    }
    assert after == before


def test_right_grade_direction_remains_observed_and_metric_endpoints_unresolved() -> None:
    scene = materialize_scene_recipe(RECIPE)
    profiles = [profile for profile in scene.terrain.profiles if profile.facade.value == "right"]

    assert len(profiles) == 1
    profile = profiles[0]
    assert profile.start_elevation is None
    assert profile.end_elevation is None
    assert profile.outward_extent is None
    assert profile.source.kind.value == "observed"
    assert any(
        "montent nettement de l'avant vers l'arriere" in evidence.observation
        for evidence in profile.evidence
    )


def test_overlay_preserves_wall_and_terrain_datums_as_distinct() -> None:
    overlay = _load(OVERLAY)
    policy = overlay["datum_policy"]

    assert "Fixed architectural wall reference" in policy["WALL_DATUM"]
    assert "rises along the right facade" in policy["TERRAIN_DATUM"]
    assert "never changes" in policy["occlusion_rule"]


def test_canonical_recipe_contains_right_facade_overlay() -> None:
    recipe = _load(RECIPE)
    assert "right-facade-grade-opening-scene-overlay-v0.1.json" in recipe["apply_overlays_in_order"]

    scene = materialize_scene_recipe(RECIPE)
    assert scene.id == recipe["scene_id"]
