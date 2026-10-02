import json
from io import BytesIO
from pathlib import Path
import subprocess
from zipfile import ZIP_STORED, ZipFile

from brickhouse.analysis_package_v1 import AnalysisPackagePhoto, build_analysis_package_v1


ROOT = Path(__file__).resolve().parents[1]
PROMPT = "PROMPT EXACT\nSans transformation."
PACKAGE_ID = "PKG_550e8400-e29b-41d4-a716-446655440000"
EXPECTED_NAMES = {
    "manifest.json",
    "prompt.txt",
    "photos/FRONT_001.jpg",
    "photos/LEFT_001.PNG",
    "photos/RIGHT_001.webp",
}


def _run_browser_builder(tmp_path: Path):
    output = tmp_path / "browser-package.zip"
    completed = subprocess.run(
        ["node", "tests/analysis_package_zip_v1_082b4.mjs", str(output)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return output, json.loads(completed.stdout.strip())


def _manifest_without_created_at(manifest: dict) -> dict:
    copy = dict(manifest)
    copy.pop("created_at")
    return copy


def test_browser_zip_is_standard_and_exact(tmp_path: Path) -> None:
    output, report = _run_browser_builder(tmp_path)

    assert report["filename"] == "BOLDUNGO_PROJECT_A_SOPHIE_R001.zip"
    assert report["prompt_text"] == PROMPT

    with ZipFile(output, "r") as archive:
        assert set(archive.namelist()) == EXPECTED_NAMES
        assert all(item.compress_type == ZIP_STORED for item in archive.infolist())

        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["schema_version"] == "boldungo.analysis-package-manifest.v1"
        assert manifest["project_id"] == "PROJECT_A"
        assert manifest["agent_id"] == "SOPHIE"
        assert manifest["agent_display_name"] == "Sophie"
        assert manifest["round_id"] == "R001"
        assert manifest["package_id"] == PACKAGE_ID
        assert manifest["created_at"].endswith("Z")
        assert manifest["prompt_path"] == "prompt.txt"
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

        assert archive.read("prompt.txt") == PROMPT.encode("utf-8")
        assert archive.read("photos/FRONT_001.jpg") == bytes.fromhex(report["photo_hex"]["FRONT_001"])
        assert archive.read("photos/LEFT_001.PNG") == bytes.fromhex(report["photo_hex"]["LEFT_001"])
        assert archive.read("photos/RIGHT_001.webp") == bytes.fromhex(report["photo_hex"]["RIGHT_001"])


def test_browser_builder_matches_python_082b2_contract(tmp_path: Path) -> None:
    output, report = _run_browser_builder(tmp_path)

    photos = [
        AnalysisPackagePhoto(
            photo_id="FRONT_001",
            primary_face="FRONT",
            original_filename="facade-originale.jpg",
            data=bytes.fromhex(report["photo_hex"]["FRONT_001"]),
            note="Vue de face",
        ),
        AnalysisPackagePhoto(
            photo_id="LEFT_001",
            primary_face="LEFT",
            original_filename="gauche-originale.PNG",
            data=bytes.fromhex(report["photo_hex"]["LEFT_001"]),
            note=None,
        ),
        AnalysisPackagePhoto(
            photo_id="RIGHT_001",
            primary_face="RIGHT",
            original_filename="droite.webp",
            data=bytes.fromhex(report["photo_hex"]["RIGHT_001"]),
            note="Angle légèrement oblique",
        ),
    ]
    python_built = build_analysis_package_v1(
        project_id="PROJECT_A",
        agent_id="SOPHIE",
        agent_display_name="Sophie",
        round_id="R001",
        package_id=PACKAGE_ID,
        photos=photos,
        prompt_text=PROMPT,
    )

    with ZipFile(output, "r") as browser_zip, ZipFile(BytesIO(python_built.zip_bytes), "r") as python_zip:
        assert set(browser_zip.namelist()) == set(python_zip.namelist()) == EXPECTED_NAMES
        browser_manifest = json.loads(browser_zip.read("manifest.json"))
        python_manifest = json.loads(python_zip.read("manifest.json"))
        assert _manifest_without_created_at(browser_manifest) == _manifest_without_created_at(python_manifest)
        assert browser_zip.read("prompt.txt") == python_zip.read("prompt.txt") == PROMPT.encode("utf-8")
        for name in EXPECTED_NAMES - {"manifest.json", "prompt.txt"}:
            assert browser_zip.read(name) == python_zip.read(name)


def test_browser_builder_has_no_network_dependency() -> None:
    source = (ROOT / "frontend" / "analysis-package-zip-v1.js").read_text(encoding="utf-8")
    lowered = source.lower()
    assert "fetch(" not in source
    assert "http://" not in lowered
    assert "https://" not in lowered
    assert "cdnjs" not in lowered
    assert "unpkg" not in lowered
    assert "filePaths.has(filePath)" in source
