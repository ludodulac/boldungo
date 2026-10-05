from __future__ import annotations

import hashlib
import json
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[2]
BENCHMARK = ROOT / "frontend" / "benchmarks" / "real-house-5"
OLD = BENCHMARK / "benchmark-3plus1"
POST = BENCHMARK / "benchmark-3plus1-post086a"
ANALYST_INPUT = POST / "analyst-input"
ANALYST_ZIP = POST / "analyst-input.zip"
LOCK = POST / "input-lock.json"
MASTER = ROOT / "frontend" / "analysis-prompt-v1-master.js"
PHOTO_MANIFEST = BENCHMARK / "manifest.json"
EXCHANGE_V1 = ROOT / "backend" / "brickhouse" / "exchange_v1.py"
PACKAGE_BUILDER = ROOT / "backend" / "brickhouse" / "analysis_package_v1.py"

SOURCE_MAIN = "1587dc75110aa1d05569379d4725ddfd56c9a2e9"
MASTER_BLOB = "69d04444a941ddffea49a23c0ce02fac0a847f02"
PHOTO_MANIFEST_BLOB = "f7e80dc8f4aa93833c66d0434423323df04a3b03"
EXCHANGE_V1_BLOB = "76792a63abf107b58cd0820a1635b669b35176f4"
PACKAGE_BUILDER_BLOB = "e88f537729fc4d217c32d44749876a78ff09a2a8"
OLD_ANALYST_ZIP_SHA256 = "d67aa1e3755de05faca509524393b09ef22305d4eaf6d34db8f3179563b63985"

PHOTO_SHA256 = {
    "FRONT_001": "81f064aa642f3e51c284473583e9c48016535177510b2cddde8f60676f87fa07",
    "RIGHT_001": "490a9058e9de9b689860256e4b9bb22f16111256106cc48fd90612c5ae3c6ec3",
    "LEFT_001": "4b53ec191f74a9c9b4c29a960eb15af60c3ad3337e8c8b19b2bab8ffe797e0dc",
    "LEFT_002": "ca8488a165ecbd687c4c2c6b42b989e57becca0c2684c01b2dd6b6bcc9c02733",
    "REAR_001": "690b83c1af13f7a68a31e5a30a1d14d9967c565c647661743ac8d46732874093",
}


def _git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def _master_prompt() -> str:
    source = MASTER.read_text(encoding="utf-8")
    tick = chr(96)
    prefix = "export const MASTER_SOPHIE_PROMPT_V1 = " + tick
    suffix = tick + ";\n"
    assert source.startswith(prefix)
    assert source.endswith(suffix)
    prompt = source[len(prefix) : -len(suffix)]
    assert "${" not in prompt
    assert tick not in prompt
    return prompt


def test_086b_source_blobs_are_exact() -> None:
    assert _git_blob_sha(MASTER.read_bytes()) == MASTER_BLOB
    assert _git_blob_sha(PHOTO_MANIFEST.read_bytes()) == PHOTO_MANIFEST_BLOB
    assert _git_blob_sha(EXCHANGE_V1.read_bytes()) == EXCHANGE_V1_BLOB
    assert _git_blob_sha(PACKAGE_BUILDER.read_bytes()) == PACKAGE_BUILDER_BLOB


def test_086b_analyst_input_has_exactly_seven_files() -> None:
    files = {p.relative_to(ANALYST_INPUT).as_posix() for p in ANALYST_INPUT.rglob("*") if p.is_file()}
    assert files == {
        "manifest.json", "prompt.txt",
        "photos/FRONT_001.jpg", "photos/RIGHT_001.jpg",
        "photos/LEFT_001.jpg", "photos/LEFT_002.jpg", "photos/REAR_001.jpg",
    }


def test_086b_photos_and_manifest_match_085_byte_for_byte() -> None:
    assert (ANALYST_INPUT / "manifest.json").read_bytes() == (OLD / "analyst-input" / "manifest.json").read_bytes()
    for photo_id, expected_sha in PHOTO_SHA256.items():
        old = OLD / "analyst-input" / "photos" / f"{photo_id}.jpg"
        new = ANALYST_INPUT / "photos" / f"{photo_id}.jpg"
        assert new.read_bytes() == old.read_bytes()
        assert hashlib.sha256(new.read_bytes()).hexdigest() == expected_sha


def test_086b_prompt_matches_post086a_master_exactly() -> None:
    assert (ANALYST_INPUT / "prompt.txt").read_text(encoding="utf-8") == _master_prompt()


def test_086b_old_zip_is_unchanged() -> None:
    assert hashlib.sha256((OLD / "analyst-input.zip").read_bytes()).hexdigest() == OLD_ANALYST_ZIP_SHA256


def test_086b_new_zip_is_frozen_and_exact() -> None:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    assert hashlib.sha256(ANALYST_ZIP.read_bytes()).hexdigest() == lock["analyst_zip"]["sha256"]
    expected = {
        "manifest.json", "prompt.txt",
        "photos/FRONT_001.jpg", "photos/RIGHT_001.jpg",
        "photos/LEFT_001.jpg", "photos/LEFT_002.jpg", "photos/REAR_001.jpg",
    }
    with ZipFile(ANALYST_ZIP, "r") as archive:
        assert len(archive.namelist()) == 7
        assert set(archive.namelist()) == expected
        for name in expected:
            assert archive.read(name) == (ANALYST_INPUT / name).read_bytes()


def test_086b_one_shared_zip_and_no_results_yet() -> None:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    assert lock["source_main_sha"] == SOURCE_MAIN
    assert lock["execution_plan"]["analyst_runs"] == ["RUN_A2", "RUN_B2", "RUN_C2"]
    assert lock["execution_plan"]["analysts_launched"] is False
    assert lock["analyst_zip"]["shared_by"] == ["RUN_A2", "RUN_B2", "RUN_C2"]
    assert "without per-run regeneration" in lock["analyst_zip"]["reuse_policy"]
    assert set(lock["result_slots"]) == {"RUN_A2", "RUN_B2", "RUN_C2"}
    assert len(set(lock["result_slots"].values())) == 3
    for rel in lock["result_slots"].values():
        assert not (ROOT / rel).exists()


def test_086b_package_has_no_extra_benchmark_payloads_or_run_specific_provenance() -> None:
    with ZipFile(ANALYST_ZIP, "r") as archive:
        names = "\n".join(archive.namelist()).casefold()
        text = (archive.read("manifest.json") + b"\n" + archive.read("prompt.txt")).decode("utf-8").casefold()
    for marker in ("runs/", "results/", "run_a2", "run_b2", "run_c2", "arbiter", "evaluator", "oracle", "retest"):
        assert marker not in names
        assert marker not in text
    assert '"human_fact_id":' not in text
    assert '"fact_text":' not in text
