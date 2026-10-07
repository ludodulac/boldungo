import json
from pathlib import Path

from brickhouse.scene import ArchitecturalScene

SCENE_PATH = Path("frontend/data/boldungo2-guided-004-real-scene.json")


def _scene():
    return ArchitecturalScene.model_validate(json.loads(SCENE_PATH.read_text(encoding="utf-8")))


def test_real_guided_004_scene_is_canonical_and_uses_current_user_metrics():
    scene = _scene()
    assert scene.schema_version == "0.2"
    assert scene.volumes[0].width.value == 9.3
    assert scene.volumes[0].width.source.kind.value == "user_provided"
    assert scene.volumes[0].depth.value == 8.2
    assert scene.volumes[0].depth.source.kind.value == "user_provided"
    assert scene.volumes[0].height.source.kind.value == "inferred"
    assert "10.0 m" not in (scene.notes or "")


def test_real_guided_004_scene_preserves_south_exterior_system_without_solid_platform_block():
    scene = _scene()
    assert len(scene.stairs) == 2
    assert [run.width for run in scene.stairs] == [1.12, 1.12]
    platform = next(item for item in scene.platforms if item.id == "south-concrete-platform")
    assert platform.thickness < 0.5
    assert platform.position.z > 2
    timber = [item for item in scene.platforms if item.material and item.material.value == "timber"]
    assert len(timber) == 2
    assert timber[1].width < timber[0].width
    assert sum(len(item.supports) for item in scene.platforms) >= 4
    assert len(scene.partial_wall_segments) >= 2


def test_real_guided_004_scene_keeps_correct_chimneys_and_deep_door_evidence():
    scene = _scene()
    assert {item.id for item in scene.chimneys} == {"west-metal-chimney-volume", "house-chimney-antenna"}
    deep = next(item for item in scene.openings if item.id == "south-deep-french-door")
    assert deep.source.kind.value == "user_provided"
    assert "deep" in (deep.opening_visual.notes or "").lower()


def test_existing_scene_viewer_can_load_persisted_scene_by_query_parameter():
    viewer = Path("frontend/scene-viewer.js").read_text(encoding="utf-8")
    assert "new URLSearchParams(window.location.search).get('scene')" in viewer
    assert "renderVolumes(); renderOpenings(); renderPlatforms();" in viewer
