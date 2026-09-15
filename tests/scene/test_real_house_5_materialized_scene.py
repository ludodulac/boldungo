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
