from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
BENCHMARK = ROOT / "frontend" / "benchmarks" / "real-house-5" / "benchmark-3plus1-post086a"
ARBITER = BENCHMARK / "arbiter-input"
ZIP = BENCHMARK / "arbiter-input.zip"

RUN_SHA = {
    "RUN_A2": "73ca340b0f391cd82ebea9a45570845952bc219e0251990046f4d96e731a1e95",
    "RUN_B2": "a6457f6d46bd3699786245de2e068351f12e98f1187e84ec676edf3095fc7f84",
    "RUN_C2": "06562a480a0ba7792b888e7b0e7806f43db476dfe0d001c8f674f5aeb9915beb",
}
PHOTO_SHA = {
    "FRONT_001": "81f064aa642f3e51c284473583e9c48016535177510b2cddde8f60676f87fa07",
    "RIGHT_001": "490a9058e9de9b689860256e4b9bb22f16111256106cc48fd90612c5ae3c6ec3",
    "LEFT_001": "4b53ec191f74a9c9b4c29a960eb15af60c3ad3337e8c8b19b2bab8ffe797e0dc",
    "LEFT_002": "ca8488a165ecbd687c4c2c6b42b989e57becca0c2684c01b2dd6b6bcc9c02733",
    "REAR_001": "690b83c1af13f7a68a31e5a30a1d14d9967c565c647661743ac8d46732874093",
}
CATEGORIES = {
    "CONSENSUS_3_OF_3", "CONSENSUS_2_OF_3", "SINGLE_DETECTION",
    "CONTRADICTION", "UNRESOLVED", "HUMAN_QUESTION_REQUIRED",
}

def test_086d_package_has_exactly_ten_files() -> None:
    files = {p.relative_to(ARBITER).as_posix() for p in ARBITER.rglob("*") if p.is_file()}
    assert files == {
        "manifest.json", "prompt.txt",
        "photos/FRONT_001.jpg", "photos/RIGHT_001.jpg",
        "photos/LEFT_001.jpg", "photos/LEFT_002.jpg", "photos/REAR_001.jpg",
        "runs/RUN_A2.json", "runs/RUN_B2.json", "runs/RUN_C2.json",
    }

def test_086d_photos_and_runs_are_exact_source_bytes() -> None:
    for photo_id, expected in PHOTO_SHA.items():
        packaged = ARBITER / "photos" / f"{photo_id}.jpg"
        source = BENCHMARK / "analyst-input" / "photos" / f"{photo_id}.jpg"
        assert packaged.read_bytes() == source.read_bytes()
        assert hashlib.sha256(packaged.read_bytes()).hexdigest() == expected
    for run_id, expected in RUN_SHA.items():
        packaged = ARBITER / "runs" / f"{run_id}.json"
        source = BENCHMARK / "results" / run_id / "analysis-result.json"
        assert packaged.read_bytes() == source.read_bytes()
        assert hashlib.sha256(packaged.read_bytes()).hexdigest() == expected

def test_086d_manifest_is_closed_world() -> None:
    manifest = json.loads((ARBITER / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["benchmark_id"] == "REAL-HOUSE-5-3PLUS1"
    assert manifest["role"] == "ARBITER"
    assert [r["run_id"] for r in manifest["runs"]] == ["RUN_A2", "RUN_B2", "RUN_C2"]
    p = manifest["provenance"]
    assert p["closed_world"] is True
    assert p["human_truth_included"] is False
    assert p["evaluator_oracle_included"] is False
    assert p["external_dependencies"] is False

def test_086d_prompt_and_manifest_are_neutral_and_categories_are_canonical() -> None:
    prompt = (ARBITER / "prompt.txt").read_text(encoding="utf-8")
    manifest = (ARBITER / "manifest.json").read_text(encoding="utf-8")
    visible = (prompt + "\n" + manifest).casefold()

    for category in CATEGORIES:
        assert category in prompt

    assert "photos as the primary source of evidence" in prompt
    assert "Never treat a majority of runs as automatic proof" in prompt
    assert "Never treat the absence of an observation from one run as an automatic contradiction" in prompt
    assert "Compare the three analyses semantically even when IDs, grouping, or wording differ" in prompt
    assert "Do not invent facts or geometry" in prompt
    assert "Preserve uncertainty whenever the photos are insufficient" in prompt

    for marker in (
        "post086a",
        "post-086a",
        "post_086a",
        "retest",
        "086a",
        "previous benchmark",
        "historical result",
        "ancienne erreur",
        "résultat attendu",
    ):
        assert marker not in visible

    assert '"source_path"' not in manifest
    assert re.search(r"\bRUN_A\b", prompt) is None
    assert re.search(r"\bRUN_B\b", prompt) is None
    assert re.search(r"\bRUN_C\b", prompt) is None

def test_086d_prompt_supports_completeness_and_entity_granularity() -> None:
    prompt = (ARBITER / "prompt.txt").read_text(encoding="utf-8")
    assert "COMPLETENESS / OMISSION" in prompt
    assert "distinct physical element is clearly visible in the photos but omitted by one or more runs" in prompt
    assert "Do not create a new category for omission" in prompt
    assert "ENTITY GRANULARITY" in prompt
    assert "multiple clearly distinct physical objects are grouped into a single entity" in prompt
    assert "loss of entity granularity" in prompt
    assert "Do not create a new category for aggregation" in prompt

def test_086d_package_excludes_historical_and_non_arbiter_artifacts() -> None:
    with ZipFile(ZIP, "r") as archive:
        names = "\n".join(archive.namelist()).casefold()
        text = (archive.read("manifest.json") + b"\n" + archive.read("prompt.txt")).decode("utf-8").casefold()
    for marker in ("results/run_a/", "results/run_b/", "results/run_c/", "arbitration-result.json", "evaluator", "oracle", "scene", "lego", "viewer"):
        assert marker not in names
    assert '"human_truth_included": false' in text

def test_086d_zip_matches_directory_and_is_stable() -> None:
    expected = {
        "manifest.json", "prompt.txt",
        "photos/FRONT_001.jpg", "photos/RIGHT_001.jpg",
        "photos/LEFT_001.jpg", "photos/LEFT_002.jpg", "photos/REAR_001.jpg",
        "runs/RUN_A2.json", "runs/RUN_B2.json", "runs/RUN_C2.json",
    }
    with ZipFile(ZIP, "r") as archive:
        assert len(archive.namelist()) == 10
        assert set(archive.namelist()) == expected
        for name in expected:
            assert archive.read(name) == (ARBITER / name).read_bytes()
    first = hashlib.sha256(ZIP.read_bytes()).hexdigest()
    second = hashlib.sha256(ZIP.read_bytes()).hexdigest()
    assert first == second
