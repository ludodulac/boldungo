from pathlib import Path

from brickhouse.scene.benchmark_scene_recipe import materialize_scene_recipe


ROOT = Path(__file__).resolve().parents[2]
REAL_HOUSE_RECIPE = ROOT / "frontend" / "benchmarks" / "real-house-5" / "scene-candidate-v0.2.json"


def test_real_house_timber_deck_preview_stays_clear_of_owner_confirmed_stair_route():
    scene = materialize_scene_recipe(REAL_HOUSE_RECIPE)
    platforms = {platform.id: platform for platform in scene.platforms}
    stairs = {stair.id: stair for stair in scene.stairs}

    timber = platforms["platform-timber-1"]
    assert timber.position.x == -2.8
    assert timber.position.y == 6.0
    assert timber.position.z == 2.1
    assert timber.width == 2.8
    assert timber.depth == 1.8
    assert timber.thickness == 0.18
    assert timber.host_volume_id == "volume_main"
    assert timber.source.kind.value == "inferred"
    assert timber.source.confidence == 0.12

    # The simplification reuses an existing Scene boundary rather than inventing
    # a hidden contour: the represented timber rectangle stops exactly where the
    # owner-confirmed westbound upper run begins.
    timber_rear_y = timber.position.y + timber.depth
    upper = stairs["stair-exterior-1-run-upper-v1"]
    assert timber_rear_y == 7.8
    assert upper.start.y == 7.8
    assert upper.end.y == 10.3
    assert timber_rear_y <= min(upper.start.y, upper.end.y)

    # Support geometry remains a low-confidence preview and is kept under the
    # simplified represented slab. No extra support is created.
    supports = {support.id: support for support in timber.supports}
    assert set(supports) == {
        "platform-timber-1-post-1",
        "platform-timber-1-post-2",
    }
    assert supports["platform-timber-1-post-1"].position.y == 6.25
    assert supports["platform-timber-1-post-1"].height == 2.1
    assert supports["platform-timber-1-post-2"].position.y == 7.45
    assert supports["platform-timber-1-post-2"].height == 2.1
    assert all(
        timber.position.y <= support.position.y
        and support.position.y + support.depth <= timber_rear_y
        for support in supports.values()
    )

    massive = platforms["platform-massive-1"]
    assert massive.position.y == 5.5
    assert massive.position.z == 2.3
    assert massive.depth == 2.3

    # This correction is deliberately local: the owner-confirmed stair route and
    # the rest of the exterior Scene stay unchanged.
    lower = stairs["stair-exterior-1-run-lower-v1"]
    assert (upper.start.x, upper.start.y, upper.start.z) == (-2.0, 7.8, 2.3)
    assert (upper.end.x, upper.end.y, upper.end.z) == (-2.0, 10.3, 1.15)
    assert (lower.start.x, lower.start.y, lower.start.z) == (-2.9, 10.3, 0.0)
    assert (lower.end.x, lower.end.y, lower.end.z) == (-2.0, 10.3, 1.15)

    assert [volume.id for volume in scene.volumes] == ["volume_main"]
    assert [wall.id for wall in scene.partial_wall_segments] == ["covered-void-right-masonry-wall-1"]
