from __future__ import annotations

import hashlib
import json
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from brickhouse.analysis_package_v1 import (
    AnalysisPackagePhoto,
    build_analysis_package_v1,
)
from brickhouse.exchange_v1 import validate_exchange_v1


ROOT = Path(__file__).resolve().parents[2]
BENCHMARK = ROOT / "frontend" / "benchmarks" / "real-house-5"
CONTROL = BENCHMARK / "benchmark-3plus1"
ANALYST_INPUT = CONTROL / "analyst-input"
LOCK = CONTROL / "input-lock.json"
MASTER = ROOT / "frontend" / "analysis-prompt-v1-master.js"
CANONICAL_MANIFEST = BENCHMARK / "manifest.json"

SOURCE_MAIN = "35d9bd979232d525bfd800b362e2fe5aaefacea3"
MASTER_BLOB = "dbc0a215a581a4bf96f7d07b12b063f5ba569fcf"
PACKAGE_ID = "PKG_085a085a-085a-4085-a085-a085a085a085"

PHOTO_MAPPING = [
    ("01-original.jpg", "FRONT_001", "FRONT"),
    ("02-original.jpg", "RIGHT_001", "RIGHT"),
    ("03-original.jpg", "LEFT_001", "LEFT"),
    ("04-original.jpg", "LEFT_002", "LEFT"),
    ("05-original.jpg", "REAR_001", "REAR"),
]


def _git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def _master_prompt() -> str:
    source = MASTER.read_text(encoding="utf-8")
    prefix = "export const MASTER_SOPHIE_PROMPT_V1 = `"
    suffix = "`;\n"
    assert source.startswith(prefix)
    assert source.endswith(suffix)
    prompt = source[len(prefix) : -len(suffix)]
    assert "${" not in prompt
    assert "`" not in prompt
    return prompt


def _frozen_manifest() -> dict:
    return json.loads((ANALYST_INPUT / "manifest.json").read_text(encoding="utf-8"))


def test_085a_lock_freezes_sources_and_does_not_launch_any_run() -> None:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    assert lock["schema_version"] == "boldungo.benchmark-3plus1-input-lock.v1"
    assert lock["mission"] == "BOLDUNGO-085A"
    assert lock["source_main_sha"] == SOURCE_MAIN
    assert lock["immutable_sources"]["master_prompt"] == {
        "path": "frontend/analysis-prompt-v1-master.js",
        "export_name": "MASTER_SOPHIE_PROMPT_V1",
        "git_blob_sha": MASTER_BLOB,
    }
    assert lock["immutable_sources"]["exchange_contract"]["schema_version"] == "boldungo.exchange.v1"
    assert lock["execution_plan"]["analyst_runs"] == ["RUN_A", "RUN_B", "RUN_C"]
    assert lock["execution_plan"]["arbiter"] == "ARBITER"
    assert lock["execution_plan"]["analysts_launched"] is False
    assert lock["execution_plan"]["arbiter_launched"] is False


def test_085a_analyst_input_contains_only_manifest_prompt_and_five_photos() -> None:
    files = {
        path.relative_to(ANALYST_INPUT).as_posix()
        for path in ANALYST_INPUT.rglob("*")
        if path.is_file()
    }
    assert files == {
        "manifest.json",
        "prompt.txt",
        "photos/FRONT_001.jpg",
        "photos/RIGHT_001.jpg",
        "photos/LEFT_001.jpg",
        "photos/LEFT_002.jpg",
        "photos/REAR_001.jpg",
    }


def test_085a_prompt_is_exactly_the_frozen_master_and_blob_identity_matches() -> None:
    master_bytes = MASTER.read_bytes()
    assert _git_blob_sha(master_bytes) == MASTER_BLOB
    assert (ANALYST_INPUT / "prompt.txt").read_text(encoding="utf-8") == _master_prompt()


def test_085a_five_photos_are_byte_for_byte_canonical_and_hash_locked() -> None:
    canonical = json.loads(CANONICAL_MANIFEST.read_text(encoding="utf-8"))
    by_name = {photo["path"]: photo for photo in canonical["photos"]}

    for source_name, photo_id, _ in PHOTO_MAPPING:
        source = BENCHMARK / source_name
        frozen = ANALYST_INPUT / "photos" / f"{photo_id}.jpg"
        assert frozen.read_bytes() == source.read_bytes()
        assert hashlib.sha256(frozen.read_bytes()).hexdigest() == by_name[source_name]["sha256"]


def test_085a_manifest_has_one_shared_neutral_sophie_identity_and_no_run_provenance() -> None:
    manifest = _frozen_manifest()
    assert set(manifest) == {
        "schema_version",
        "project_id",
        "agent_id",
        "agent_display_name",
        "round_id",
        "package_id",
        "created_at",
        "prompt_path",
        "photos",
    }
    assert manifest["schema_version"] == "boldungo.analysis-package-manifest.v1"
    assert manifest["project_id"] == "REAL-HOUSE-5-3PLUS1"
    assert manifest["agent_id"] == "SOPHIE"
    assert manifest["agent_display_name"] == "Sophie"
    assert manifest["round_id"] == "R001"
    assert manifest["package_id"] == PACKAGE_ID
    assert manifest["prompt_path"] == "prompt.txt"

    assert manifest["photos"] == [
        {
            "photo_id": photo_id,
            "file_path": f"photos/{photo_id}.jpg",
            "primary_face": face,
            "original_filename": source_name,
            "note": None,
        }
        for source_name, photo_id, face in PHOTO_MAPPING
    ]

    serialized = json.dumps(manifest, ensure_ascii=False).casefold()
    for marker in (
        "run_a",
        "run_b",
        "run_c",
        "arbiter",
        "oracle",
        "evaluator",
        "owner_fact",
        "human_answer",
        "human_correction",
        "scene-candidate",
        "materialized-scene",
    ):
        assert marker not in serialized


def test_085a_frozen_directory_matches_existing_v1_package_builder_contract() -> None:
    frozen_manifest = _frozen_manifest()
    built = build_analysis_package_v1(
        project_id=frozen_manifest["project_id"],
        agent_id=frozen_manifest["agent_id"],
        agent_display_name=frozen_manifest["agent_display_name"],
        round_id=frozen_manifest["round_id"],
        package_id=frozen_manifest["package_id"],
        photos=[
            AnalysisPackagePhoto(
                photo_id=photo_id,
                primary_face=face,
                original_filename=source_name,
                data=(BENCHMARK / source_name).read_bytes(),
                note=None,
            )
            for source_name, photo_id, face in PHOTO_MAPPING
        ],
        prompt_text=(ANALYST_INPUT / "prompt.txt").read_text(encoding="utf-8"),
    )

    assert built.filename == "BOLDUNGO_REAL-HOUSE-5-3PLUS1_SOPHIE_R001.zip"
    with ZipFile(BytesIO(built.zip_bytes), "r") as archive:
        assert set(archive.namelist()) == {
            "manifest.json",
            "prompt.txt",
            "photos/FRONT_001.jpg",
            "photos/RIGHT_001.jpg",
            "photos/LEFT_001.jpg",
            "photos/LEFT_002.jpg",
            "photos/REAR_001.jpg",
        }
        generated_manifest = json.loads(archive.read("manifest.json"))
        generated_manifest["created_at"] = frozen_manifest["created_at"]
        assert generated_manifest == frozen_manifest
        assert archive.read("prompt.txt") == (ANALYST_INPUT / "prompt.txt").read_bytes()
        for _, photo_id, _ in PHOTO_MAPPING:
            assert archive.read(f"photos/{photo_id}.jpg") == (
                ANALYST_INPUT / "photos" / f"{photo_id}.jpg"
            ).read_bytes()


def test_085a_frozen_identity_accepts_a_valid_exchange_v1_analysis_result() -> None:
    manifest = _frozen_manifest()
    result = {
        "schema_version": "boldungo.exchange.v1",
        "message_type": "ANALYSIS_RESULT",
        "project_id": manifest["project_id"],
        "agent_id": manifest["agent_id"],
        "agent_display_name": manifest["agent_display_name"],
        "round_id": manifest["round_id"],
        "package_id": manifest["package_id"],
        "created_at": "2026-10-04T11:30:00Z",
        "payload": {
            "analysis": {
                "observations": [],
                "human_facts": [],
                "entities": [],
                "relations": [],
                "uncertainties": [],
            },
            "questions": [],
        },
    }
    assert validate_exchange_v1(result) == {
        "status": "VALID ANALYSIS_RESULT",
        "reason": None,
    }
