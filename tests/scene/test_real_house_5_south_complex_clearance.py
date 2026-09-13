from pathlib import Path

from brickhouse.partial_scene_pipeline import run_partial_scene_pipeline
from brickhouse.scene.benchmark_scene_recipe import materialize_scene_recipe


ROOT = Path(__file__).resolve().parents[2]
RECIPE = ROOT / "frontend" / "benchmarks" / "real-house-5" / "scene-candidate-v0.2.json"


def _scene():
    return materialize_scene_recipe(RECIPE)


def test_south_complex_preserves_long_timber_extent_and_clears_upper_stair() -> None:
    scene = _scene()
    platforms = {item.id: item for item in scene.platforms}
    stairs = {item.id: item for item in scene.stairs}

    timber_wall = platforms["platform-timber-1"]
    timber_outer = platforms["platform-timber-1-outer-front-fragment"]
    landing = platforms["platform-massive-1"]
    upper = stairs["stair-exterior-1-run-upper-v1"]

    assert timber_wall.position.y == 6.0
    assert timber_wall.position.y + timber_wall.depth == 9.0
    assert timber_wall.position.z == 2.1
    assert landing.position.z == 2.3

    assert timber_outer.position.y == 6.0
    assert timber_outer.position.y + timber_outer.depth == 7.8
    assert upper.end.y == 7.8
    assert upper.start.y == 10.3

    # The upper stair corridor is centered at x=-2.0 with width 1.0. The long
    # wall-side timber strip starts beyond that corridor, while the wider outer
    # timber fragment stops at the landing/stair junction y=7.8.
    stair_x_min = upper.start.x - upper.width / 2
    stair_x_max = upper.start.x + upper.width / 2
    timber_wall_x_min = timber_wall.position.x
    timber_wall_x_max = timber_wall.position.x + timber_wall.width
    assert timber_wall_x_min >= stair_x_max
    assert timber_outer.position.y + timber_outer.depth <= upper.end.y

    # Masonry landing stays distinct and unchanged at the stair arrival.
    assert landing.position.x == -2.2
    assert landing.position.y == 5.5
    assert landing.width == 2.2
    assert landing.depth == 2.3
    assert upper.end.z == landing.position.z


def test_south_complex_scene_still_generates_complete_partial_brickmodel() -> None:
    scene = _scene()
    bundle = run_partial_scene_pipeline(scene, front_width_studs=48)
    ids = [part.placement_id for part in bundle.brick_model.parts]

    assert bundle.brick_model.parts
    assert bundle.bom.total_parts == len(bundle.brick_model.parts)
    assert any(value.startswith("scene-platform:platform-timber-1:") for value in ids)
    assert any("platform-timber-1-outer-front-fragment" in value for value in ids)
    assert any("platform-massive-1" in value for value in ids)
    assert any("stair-exterior-1-run-upper-v1" in value for value in ids)
    assert any("stair-exterior-1-run-lower-v1" in value for value in ids)
