from __future__ import annotations

import hashlib
import json
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[2]
CONTROL = ROOT / "frontend" / "benchmarks" / "real-house-5" / "benchmark-3plus1"
ANALYST_INPUT = CONTROL / "analyst-input"
ARBITER_INPUT = CONTROL / "arbiter-input"
ARBITER_ZIP = CONTROL / "arbiter-input.zip"
LOCK = CONTROL / "input-lock.json"
MASTER = ROOT / "frontend" / "analysis-prompt-v1-master.js"
EXCHANGE_V1 = ROOT / "backend" / "brickhouse" / "exchange_v1.py"

MASTER_BLOB = "dbc0a215a581a4bf96f7d07b12b063f5ba569fcf"
EXCHANGE_V1_BLOB = "76792a63abf107b58cd0820a1635b669b35176f4"
ANALYST_ZIP_SHA256 = "d67aa1e3755de05faca509524393b09ef22305d4eaf6d34db8f3179563b63985"

PHOTO_SHA256 = {
    "FRONT_001": "81f064aa642f3e51c284473583e9c48016535177510b2cddde8f60676f87fa07",
    "RIGHT_001": "490a9058e9de9b689860256e4b9bb22f16111256106cc48fd90612c5ae3c6ec3",
    "LEFT_001": "4b53ec191f74a9c9b4c29a960eb15af60c3ad3337e8c8b19b2bab8ffe797e0dc",
    "LEFT_002": "ca8488a165ecbd687c4c2c6b42b989e57becca0c2684c01b2dd6b6bcc9c02733",
    "REAR_001": "690b83c1af13f7a68a31e5a30a1d14d9967c565c647661743ac8d46732874093",
}

RUN_SHA256 = {
    "RUN_A": "1c5669b97b5a5dd5e4b27171b4ce8920d6a83f5890a049317bf9ae07ced56932",
    "RUN_B": "bd08a70d08ea40eb8390a8d8996f3fa1e5b835df3f24f197cdfc9582c9c05a47",
    "RUN_C": "769c75bf03742dec996b4143b5697aefd9ea2c430eb1ac92c81eb4cc98a4842c",
}


def _git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def test_085e_arbiter_directory_contains_only_neutral_package_files() -> None:
    files = {
        path.relative_to(ARBITER_INPUT).as_posix()
        for path in ARBITER_INPUT.rglob("*")
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
        "runs/RUN_A.json",
        "runs/RUN_B.json",
        "runs/RUN_C.json",
    }

    lowered_paths = "\n".join(sorted(files)).casefold()
    for forbidden in ("evaluator", "oracle", "human-answer", "human-correction"):
        assert forbidden not in lowered_paths


def test_085e_photos_are_byte_identical_to_frozen_analyst_photos() -> None:
    for photo_id, expected_sha in PHOTO_SHA256.items():
        source = ANALYST_INPUT / "photos" / f"{photo_id}.jpg"
        copied = ARBITER_INPUT / "photos" / f"{photo_id}.jpg"
        assert copied.read_bytes() == source.read_bytes()
        assert hashlib.sha256(copied.read_bytes()).hexdigest() == expected_sha


def test_085e_runs_are_byte_identical_to_canonical_results() -> None:
    for run_id, expected_sha in RUN_SHA256.items():
        source = CONTROL / "results" / run_id / "analysis-result.json"
        copied = ARBITER_INPUT / "runs" / f"{run_id}.json"
        assert copied.read_bytes() == source.read_bytes()
        assert hashlib.sha256(source.read_bytes()).hexdigest() == expected_sha
        assert hashlib.sha256(copied.read_bytes()).hexdigest() == expected_sha


def test_085e_manifest_freezes_closed_world_provenance() -> None:
    manifest = json.loads((ARBITER_INPUT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["benchmark_id"] == "REAL-HOUSE-5-3PLUS1"
    assert manifest["role"] == "ARBITER"
    assert manifest["prompt_path"] == "prompt.txt"
    assert manifest["provenance"] == {
        "closed_world": True,
        "allowed_input_classes": ["photos", "run_results", "prompt"],
        "human_truth_included": False,
        "evaluator_oracle_included": False,
        "external_dependencies": False,
    }

    assert {item["photo_id"]: item["sha256"] for item in manifest["photos"]} == PHOTO_SHA256
    assert {item["run_id"]: item["sha256"] for item in manifest["runs"]} == RUN_SHA256


def test_085e_prompt_encodes_neutral_arbitration_rules() -> None:
    prompt = (ARBITER_INPUT / "prompt.txt").read_text(encoding="utf-8")
    required = (
        "Treat the photos as the primary source of evidence.",
        "Never treat a majority of runs as automatic proof.",
        "Never treat the absence of an observation from one run as an automatic contradiction.",
        "Do not invent facts or geometry.",
        "Use only the files contained in this package.",
        "boldungo.benchmark-3plus1-arbitration.v1",
        "CONSENSUS_3_OF_3",
        "CONSENSUS_2_OF_3",
        "SINGLE_DETECTION",
        "CONTRADICTION",
        "UNRESOLVED",
        "HUMAN_QUESTION_REQUIRED",
        "SUPPORTED",
        "PARTIALLY_SUPPORTED",
        "NOT_SUPPORTED",
        "INSUFFICIENT",
    )
    for marker in required:
        assert marker in prompt


def test_085e_zip_is_exact_and_hash_locked() -> None:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    arbiter_lock = lock["arbiter_input"]
    assert arbiter_lock["path"] == (
        "frontend/benchmarks/real-house-5/benchmark-3plus1/arbiter-input/"
    )
    assert arbiter_lock["zip_path"] == (
        "frontend/benchmarks/real-house-5/benchmark-3plus1/arbiter-input.zip"
    )
    assert arbiter_lock["result_path"] == lock["result_slots"]["ARBITER"]
    assert hashlib.sha256(ARBITER_ZIP.read_bytes()).hexdigest() == arbiter_lock["zip_sha256"]

    expected = {
        "manifest.json",
        "prompt.txt",
        "photos/FRONT_001.jpg",
        "photos/RIGHT_001.jpg",
        "photos/LEFT_001.jpg",
        "photos/LEFT_002.jpg",
        "photos/REAR_001.jpg",
        "runs/RUN_A.json",
        "runs/RUN_B.json",
        "runs/RUN_C.json",
    }
    with ZipFile(ARBITER_ZIP, "r") as archive:
        assert len(archive.namelist()) == 10
        assert set(archive.namelist()) == expected
        for name in expected:
            assert archive.read(name) == (ARBITER_INPUT / name).read_bytes()


def test_085e_existing_frozen_inputs_and_contracts_remain_unchanged() -> None:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))

    assert hashlib.sha256((CONTROL / "analyst-input.zip").read_bytes()).hexdigest() == ANALYST_ZIP_SHA256
    assert _git_blob_sha(MASTER.read_bytes()) == MASTER_BLOB
    assert _git_blob_sha(EXCHANGE_V1.read_bytes()) == EXCHANGE_V1_BLOB
    assert lock["execution_plan"]["arbiter_launched"] is False

    for run_id, expected_sha in RUN_SHA256.items():
        assert lock["arbiter_input"]["runs"][run_id]["sha256"] == expected_sha
        source = CONTROL / "results" / run_id / "analysis-result.json"
        assert hashlib.sha256(source.read_bytes()).hexdigest() == expected_sha
