from pathlib import Path

from brickhouse.scene.benchmark_scene_recipe import materialize_scene_recipe


ROOT = Path(__file__).resolve().parents[2]
REAL_HOUSE_RECIPE = ROOT / "frontend" / "benchmarks" / "real-house-5" / "scene-candidate-v0.2.json"


def test_real_house_timber_deck_keeps_longitudinal_extent_after_local_clearance():
    scene = materialize_scene_recipe(REAL_HOUSE_RECIPE)
    platforms = {platform.id: platform for platform in scene.platforms}

    timber = platforms["platform-timber-1"]
    assert timber.position.x == -1.4
    assert timber.position.y == 6.0
    assert timber.position.z == 2.1
    assert timber.width == 1.4
    assert timber.depth == 3.0
    assert timber.position.y + timber.depth == 9.0
    assert timber.thickness == 0.18
    assert timber.host_volume_id == "volume_main"
    assert timber.source.kind.value == "inferred"
    assert timber.source.confidence == 0.12

    outer = platforms["platform-timber-1-outer-front-fragment"]
    assert outer.position.x == -2.8
    assert outer.position.y == 6.0
    assert outer.position.z == 2.1
    assert outer.width == 1.4
    assert outer.depth == 1.8
    assert outer.position.y + outer.depth == 7.8

    supports = {
        support.id: support
        for platform in (timber, outer)
        for support in platform.supports
    }
    assert supports["platform-timber-1-post-1"].position.y == 6.25
    assert supports["platform-timber-1-post-1"].height == 2.1
    assert supports["platform-timber-1-post-2"].position.y == 8.65
    assert supports["platform-timber-1-post-2"].height == 2.1

    massive = platforms["platform-massive-1"]
    assert massive.position.y == 5.5
    assert massive.position.z == 2.3
    assert massive.depth == 2.3

    assert [volume.id for volume in scene.volumes] == ["volume_main"]
    assert [wall.id for wall in scene.partial_wall_segments] == ["covered-void-right-masonry-wall-1"]
    assert {stair.id for stair in scene.stairs} == {
        "stair-exterior-1-run-lower-v1",
        "stair-exterior-1-run-upper-v1",
    }


def test_real_house_timber_deck_exposed_front_edge_keeps_observed_railing():
    scene = materialize_scene_recipe(REAL_HOUSE_RECIPE)
    platforms = {platform.id: platform for platform in scene.platforms}

    outer = platforms["platform-timber-1-outer-front-fragment"]
    assert outer.edges is not None
    assert outer.edges.x_min.treatment.value == "open_railing"
    assert outer.edges.y_min.treatment.value == "open_railing"
