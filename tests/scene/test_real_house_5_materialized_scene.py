import json
from pathlib import Path

from brickhouse.scene.benchmark_scene_recipe import materialize_scene_recipe

ROOT = Path(__file__).resolve().parents[2]
BENCHMARK = ROOT / "frontend" / "benchmarks" / "real-house-5"
RECIPE = BENCHMARK / "scene-candidate-v0.2.json"
MATERIALIZED = BENCHMARK / "materialized-scene-v0.2.json"


def test_published_materialized_scene_matches_current_recipe() -> None:
    expected = materialize_scene_recipe(RECIPE).model_dump(mode="json")
    actual = json.loads(MATERIALIZED.read_text(encoding="utf-8"))
    assert actual == expected


def test_timber_deck_preserves_support_truth_without_invented_metric_posts() -> None:
    scene = materialize_scene_recipe(RECIPE)
    timber = next(platform for platform in scene.platforms if platform.id == "platform-timber-1")
    fragment = next(platform for platform in scene.platforms if platform.id == "platform-timber-1-outer-front-fragment")
    assert timber.supports == []
    assert fragment.supports == []

    observations = [
        item for item in scene.platform_structure_observations
        if item.platform_id == "platform-timber-1"
    ]
    assert {item.kind.value for item in observations} == {"vertical_post", "diagonal_brace"}
    assert all(item.count is None for item in observations)
