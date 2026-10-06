from io import BytesIO
import json
from zipfile import ZIP_STORED, ZipFile

from brickhouse.guided_scene_v1 import (
    GUIDED_HOUSE_SCHEMA_VERSION,
    PROVENANCE_LEVELS,
    parse_guided_house_package_v1,
    reconstruct_guided_house_package_v1,
)
from brickhouse.scene import ArchitecturalScene


def _fixture():
    guided = {
        "schema_version": GUIDED_HOUSE_SCHEMA_VERSION,
        "project_id": "GUIDED_FIXTURE",
        "package_id": "GUIDED_FIXTURE_001",
        "known_front_width": 10.0,
        "general_notes": "fixture technique",
        "photos": [{
            "photo_id": "FRONT_001",
            "orientation": "FRONT",
            "description": "Façade avant",
            "must_reproduce": ["porte centrale"],
            "do_not_confuse": [],
            "known_dimensions": ["hauteur: 6.2 m"],
            "connections_to_other_photos": [],
            "provenance": "USER_CONFIRMED",
            "original_filename": "front.jpg",
            "file_path": "photos/FRONT_001.jpg",
        }],
    }
    manifest = {
        "schema_version": GUIDED_HOUSE_SCHEMA_VERSION,
        "project_id": "GUIDED_FIXTURE",
        "package_id": "GUIDED_FIXTURE_001",
        "guided_data_path": "guided-house.json",
        "photos": [{"photo_id": "FRONT_001", "file_path": "photos/FRONT_001.jpg", "original_filename": "front.jpg"}],
    }
    original = b"\xff\xd8GUIDED-ORIGINAL-PHOTO\xff\xd9"
    out = BytesIO()
    with ZipFile(out, "w", compression=ZIP_STORED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest))
        archive.writestr("guided-house.json", json.dumps(guided))
        archive.writestr("photos/FRONT_001.jpg", original)
    return out.getvalue(), original


def test_guided_package_to_existing_architectural_scene_contract():
    package_bytes, original = _fixture()
    parsed = parse_guided_house_package_v1(package_bytes)
    assert parsed.photos["FRONT_001"] == original
    assert parsed.guided["photos"][0]["provenance"] == "USER_CONFIRMED"
    assert PROVENANCE_LEVELS == ("USER_CONFIRMED", "PHOTO", "INFERRED", "UNKNOWN")

    scene = reconstruct_guided_house_package_v1(package_bytes, candidates={
        "front_width": {"value": 7.4, "provenance": "INFERRED"},
        "depth": {"value": 8.0, "provenance": "PHOTO", "evidence": [{"photo_index": 1, "observation": "visible side depth"}]},
    })
    assert isinstance(scene, ArchitecturalScene)
    assert scene.schema_version == "0.2"
    assert scene.volumes[0].width.value == 10.0
    assert scene.volumes[0].width.source.kind.value == "user_provided"
    assert scene.volumes[0].depth.value == 8.0
    assert scene.volumes[0].depth.source.kind.value == "observed"
    assert scene.volumes[0].height.value == 6.2
    assert scene.volumes[0].height.source.kind.value == "user_provided"

    payload = scene.model_dump(mode="json")
    assert payload["schema_version"] == "0.2"
    assert isinstance(payload["volumes"], list) and payload["volumes"]


def test_scene_viewer_accepts_same_contract():
    viewer = open("frontend/scene-viewer.js", encoding="utf-8").read()
    assert "candidate?.schema_version === '0.2' && Array.isArray(candidate.volumes)" in viewer
