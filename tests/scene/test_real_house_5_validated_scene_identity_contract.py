import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCENE_PATH = ROOT / "frontend" / "benchmarks" / "real-house-5" / "brickhouse-scene-result-hydrated-validated.json"


def test_validated_real_house_scene_preserves_survey_access_identities_and_topology():
    scene = json.loads(SCENE_PATH.read_text(encoding="utf-8"))
    platform_ids = {item["id"] for item in scene["platforms"]}
    stair_ids = {item["id"] for item in scene["stairs"]}

    assert "platform-massive-1" in platform_ids
    assert "platform-timber-1" in platform_ids
    assert "stair-exterior-1" in stair_ids
    assert "platform-masonry-landing-1" not in platform_ids
    assert "platform-timber-deck-1" not in platform_ids

    relation = next(item for item in scene["relations"] if item["id"] == "relation-stair-landing")
    assert relation["kind"] == "connects_to"
    assert relation["subject_id"] == "stair-exterior-1"
    assert relation["object_id"] == "platform-massive-1"
    assert relation["certainty"] == "certain"
    assert relation["geometry_status"] == "unresolved"


def test_landing_identity_is_not_replaced_by_a_volume_endpoint():
    scene = json.loads(SCENE_PATH.read_text(encoding="utf-8"))
    stair_relations = [
        item for item in scene["relations"]
        if item["kind"] == "connects_to" and item["subject_id"] == "stair-exterior-1"
    ]
    assert any(item["object_id"] == "platform-massive-1" for item in stair_relations)
    assert not any(item["object_id"] == "lower_exterior_volume" for item in stair_relations)
