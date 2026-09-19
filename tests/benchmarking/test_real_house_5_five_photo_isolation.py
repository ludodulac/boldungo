from __future__ import annotations

import json
from pathlib import Path

import pytest

from brickhouse.benchmarking.five_photo import (
    Deductibility,
    Diagnostic,
    classify_diagnostic,
    freeze_candidate_output,
    load_oracle_after_candidate,
    stage_candidate_inputs,
)

ROOT = Path(__file__).resolve().parents[2]
BENCHMARK = ROOT / "frontend" / "benchmarks" / "real-house-5"
MANIFEST = BENCHMARK / "manifest.json"
ORACLE = BENCHMARK / "evaluator" / "private-five-photo-oracle-v0.1.json"

CANONICAL_HASHES = {
    1: "81f064aa642f3e51c284473583e9c48016535177510b2cddde8f60676f87fa07",
    2: "490a9058e9de9b689860256e4b9bb22f16111256106cc48fd90612c5ae3c6ec3",
    3: "4b53ec191f74a9c9b4c29a960eb15af60c3ad3337e8c8b19b2bab8ffe797e0dc",
    4: "ca8488a165ecbd687c4c2c6b42b989e57becca0c2684c01b2dd6b6bcc9c02733",
    5: "690b83c1af13f7a68a31e5a30a1d14d9967c565c647661743ac8d46732874093",
}

FORBIDDEN_CANDIDATE_NAMES = {
    "accepted-survey-v0.1.json",
    "scene-source-survey-v0.1.json",
    "owner-spatial-topology-survey-facts-v0.1.json",
    "materialized-scene-v0.2.json",
    "private-five-photo-oracle-v0.1.json",
}


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_historical_five_photo_identity_is_frozen():
    photos = _manifest()["photos"]
    assert [photo["photo_index"] for photo in photos] == [1, 2, 3, 4, 5]
    assert {photo["photo_index"]: photo["sha256"] for photo in photos} == CANONICAL_HASHES


def test_candidate_workspace_contains_exactly_five_canonical_images_and_no_oracle(tmp_path):
    manifest = _manifest()
    candidate = tmp_path / "candidate"
    staged_manifest = stage_candidate_inputs(
        source_dir=BENCHMARK,
        candidate_dir=candidate,
        expected_photos=manifest["photos"],
    )
    staged = json.loads(staged_manifest.read_text(encoding="utf-8"))
    assert [photo["photo_index"] for photo in staged["photos"]] == [1, 2, 3, 4, 5]
    assert len(list((candidate / "images").glob("*"))) == 5
    assert {p.name for p in candidate.rglob("*") if p.is_file()} == {
        "candidate-input.json",
        "01-original.jpg",
        "02-original.jpg",
        "03-original.jpg",
        "04-original.jpg",
        "05-original.jpg",
    }
    assert not ({p.name for p in candidate.rglob("*")} & FORBIDDEN_CANDIDATE_NAMES)


def test_candidate_stager_rejects_photo_indexes_6_to_22(tmp_path):
    photos = list(_manifest()["photos"])
    photos[-1] = dict(photos[-1], photo_index=6)
    with pytest.raises(ValueError, match="outside 1..5"):
        stage_candidate_inputs(
            source_dir=BENCHMARK,
            candidate_dir=tmp_path / "candidate",
            expected_photos=photos,
        )


def test_oracle_can_only_be_loaded_after_candidate_output_is_frozen(tmp_path):
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    output = candidate / "candidate-output.json"
    with pytest.raises(RuntimeError, match="must be frozen"):
        load_oracle_after_candidate(candidate_output=output, oracle_path=ORACLE)

    frozen = freeze_candidate_output(candidate, {"schema_version": "baseline-placeholder"})
    oracle = load_oracle_after_candidate(candidate_output=frozen, oracle_path=ORACLE)
    assert oracle["benchmark_id"] == "real-house-5"


def test_unknown_from_five_accepts_honest_unknown():
    assert classify_diagnostic(
        maximum_from_five=Deductibility.UNKNOWN_FROM_5,
        candidate_state="unknown",
    ) is Diagnostic.D


def test_unknown_from_five_rejects_invented_certainty_as_g():
    assert classify_diagnostic(
        maximum_from_five=Deductibility.UNKNOWN_FROM_5,
        candidate_state="certain",
    ) is Diagnostic.G


def test_observable_architecture_missed_is_e_and_wrong_interpretation_is_f():
    assert classify_diagnostic(
        maximum_from_five=Deductibility.OBSERVABLE_5,
        candidate_state="missed",
    ) is Diagnostic.E
    assert classify_diagnostic(
        maximum_from_five=Deductibility.OBSERVABLE_5,
        candidate_state="interpreted",
        interpretation_correct=False,
    ) is Diagnostic.F


def test_oracle_declares_control_photos_private_and_has_no_global_score():
    oracle = json.loads(ORACLE.read_text(encoding="utf-8"))
    policy = oracle["candidate_input_policy"]
    assert policy["allowed_photo_indexes"] == [1, 2, 3, 4, 5]
    assert policy["control_photo_indexes"] == list(range(6, 23))
    assert policy["owner_facts_allowed"] is False
    assert policy["scene_allowed"] is False
    assert policy["lego_allowed"] is False
    assert "score" not in oracle
    assert "weights" not in oracle


def test_oracle_has_explicit_deductibility_and_perceptual_importance():
    oracle = json.loads(ORACLE.read_text(encoding="utf-8"))
    truths = oracle["truths"]
    assert len(truths) == 23
    assert {truth["maximum_from_five"] for truth in truths} == {
        "OBSERVABLE_5",
        "MULTIVIEW_DEDUCIBLE_5",
        "HYPOTHESIS_ONLY_5",
        "UNKNOWN_FROM_5",
    }
    assert {truth["importance"] for truth in truths} == {
        "CRITICAL",
        "IMPORTANT",
        "SECONDARY",
    }
    for truth in truths:
        assert all(1 <= index <= 5 for index in truth["evidence_1_5"])
        assert all(6 <= index <= 22 for index in truth["evidence_6_22"])
