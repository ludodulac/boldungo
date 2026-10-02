import json
from io import BytesIO
from zipfile import ZipFile

import pytest

from brickhouse.analysis_package_v1 import AnalysisPackagePhoto, build_analysis_package_v1


PACKAGE_ID = "PKG_550e8400-e29b-41d4-a716-446655440000"


@pytest.fixture
def fake_photos() -> list[AnalysisPackagePhoto]:
    return [
        AnalysisPackagePhoto(
            photo_id="FRONT_001",
            primary_face="FRONT",
            original_filename="facade-originale.jpg",
            data=b"\\xff\\xd8FAKE-JPEG-FRONT\\xff\\xd9",
            note="Vue de face",
        ),
        AnalysisPackagePhoto(
            photo_id="LEFT_001",
            primary_face="LEFT",
            original_filename="gauche-originale.PNG",
            data=b"\\x89PNG\\r\\nFAKE-LEFT",
            note=None,
        ),
        AnalysisPackagePhoto(
            photo_id="RIGHT_001",
            primary_face="RIGHT",
            original_filename="droite.webp",
            data=b"RIFF-FAKE-WEBP",
            note="Angle légèrement oblique",
        ),
    ]


def _build(fake_photos, prompt_text="PROMPT EXACT\\nSans transformation."):
    return build_analysis_package_v1(
        project_id="PROJECT_A",
        agent_id="SOPHIE",
        agent_display_name="Sophie",
        round_id="R001",
        package_id=PACKAGE_ID,
        photos=fake_photos,
        prompt_text=prompt_text,
    )


def test_builds_exact_minimal_zip_and_preserves_input_bytes(fake_photos) -> None:
    prompt = "PROMPT EXACT\\nSans transformation."
    built = _build(fake_photos, prompt)

    assert built.filename == "BOLDUNGO_PROJECT_A_SOPHIE_R001.zip"

    with ZipFile(BytesIO(built.zip_bytes), "r") as archive:
        assert set(archive.namelist()) == {
            "manifest.json",
            "prompt.txt",
            "photos/FRONT_001.jpg",
            "photos/LEFT_001.PNG",
            "photos/RIGHT_001.webp",
        }
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["schema_version"] == "boldungo.analysis-package-manifest.v1"
        assert manifest["project_id"] == "PROJECT_A"
        assert manifest["agent_id"] == "SOPHIE"
        assert manifest["agent_display_name"] == "Sophie"
        assert manifest["round_id"] == "R001"
        assert manifest["package_id"] == PACKAGE_ID
        assert manifest["prompt_path"] == "prompt.txt"
        assert manifest["created_at"].endswith("Z")
        assert manifest["photos"] == [
            {
                "photo_id": "FRONT_001",
                "file_path": "photos/FRONT_001.jpg",
                "primary_face": "FRONT",
                "original_filename": "facade-originale.jpg",
                "note": "Vue de face",
            },
            {
                "photo_id": "LEFT_001",
                "file_path": "photos/LEFT_001.PNG",
                "primary_face": "LEFT",
                "original_filename": "gauche-originale.PNG",
                "note": None,
            },
            {
                "photo_id": "RIGHT_001",
                "file_path": "photos/RIGHT_001.webp",
                "primary_face": "RIGHT",
                "original_filename": "droite.webp",
                "note": "Angle légèrement oblique",
            },
        ]
        assert archive.read("prompt.txt") == prompt.encode("utf-8")
        for photo, manifest_entry in zip(fake_photos, manifest["photos"], strict=True):
            assert archive.read(manifest_entry["file_path"]) == photo.data


@pytest.mark.parametrize(
    ("photos", "match"),
    [
        ([], "at least one photo"),
        (
            [
                AnalysisPackagePhoto("FRONT_001", "FRONT", "a.jpg", b"a"),
                AnalysisPackagePhoto("FRONT_001", "FRONT", "b.png", b"b"),
            ],
            "duplicate photo_id",
        ),
        (
            [AnalysisPackagePhoto("FRONT_001", "SIDE", "a.jpg", b"a")],
            "invalid primary_face",
        ),
        (
            [AnalysisPackagePhoto("FRONT_001", "FRONT", "no-extension", b"a")],
            "cannot determine",
        ),
        (
            [AnalysisPackagePhoto("FRONT_001", "FRONT", "a.jpg", b"")],
            "non-empty binary data",
        ),
    ],
)
def test_rejects_invalid_photo_inputs(photos, match) -> None:
    with pytest.raises(ValueError, match=match):
        _build(photos)


def test_rejects_invalid_package_id(fake_photos) -> None:
    with pytest.raises(ValueError, match="PKG_<UUIDv4>"):
        build_analysis_package_v1(
            project_id="PROJECT_A",
            agent_id="SOPHIE",
            agent_display_name="Sophie",
            round_id="R001",
            package_id="PKG_NOT-A-UUID",
            photos=fake_photos,
            prompt_text="prompt",
        )
