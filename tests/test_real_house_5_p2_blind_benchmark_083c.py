import hashlib
import json
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from brickhouse.blind_benchmark_v1 import build_real_house_5_p2_blind_package
from brickhouse.exchange_v1 import validate_exchange_v1


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_ROOT = ROOT / "frontend" / "benchmarks" / "real-house-5"
CHALLENGE_ROOT = BENCHMARK_ROOT / "blind-p2"
CHALLENGE = CHALLENGE_ROOT / "challenge-input.json"
PROMPT = CHALLENGE_ROOT / "prompt.txt"
PHOTO = BENCHMARK_ROOT / "02-original.jpg"
EVALUATOR = BENCHMARK_ROOT / "evaluator" / "blind-p2-evaluator-v0.1.json"
BUILDER = ROOT / "backend" / "brickhouse" / "blind_benchmark_v1.py"

PACKAGE_ID = "PKG_123e4567-e89b-42d3-a456-426614174000"
PHOTO_SHA256 = "490a9058e9de9b689860256e4b9bb22f16111256106cc48fd90612c5ae3c6ec3"

FORBIDDEN_PACKAGE_MARKERS = (
    "scene-candidate-v0.2.json",
    "materialized-scene-v0.2.json",
    "accepted-survey",
    "confirmed-opening-semantics-overlay",
    "right-facade-grade-opening-scene-overlay",
    "human_facts",
    "right-opening-2",
    "right-opening-3",
    "local_grade_clearance",
    "glass_block",
    "pavés de verre",
    "paves de verre",
    "blocs translucides",
    "contact trottoir",
    "terrain montant vers l'arrière",
    "terrain montant vers l’arrière",
    "montent nettement de l'avant vers l'arriere",
)


def _built_zip():
    built = build_real_house_5_p2_blind_package(package_id=PACKAGE_ID)
    return built, ZipFile(BytesIO(built.zip_bytes), "r")


def test_blind_package_contains_only_manifest_prompt_and_original_p2() -> None:
    built, archive = _built_zip()
    with archive:
        assert built.filename == "BOLDUNGO_REAL-HOUSE-5-P2-BLIND_SOPHIE_R001.zip"
        assert set(archive.namelist()) == {
            "manifest.json",
            "prompt.txt",
            "photos/RIGHT_001.jpg",
        }

        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["schema_version"] == "boldungo.analysis-package-manifest.v1"
        assert manifest["project_id"] == "REAL-HOUSE-5-P2-BLIND"
        assert manifest["agent_id"] == "SOPHIE"
        assert manifest["agent_display_name"] == "Sophie"
        assert manifest["round_id"] == "R001"
        assert manifest["package_id"] == PACKAGE_ID
        assert manifest["prompt_path"] == "prompt.txt"
        assert manifest["photos"] == [
            {
                "photo_id": "RIGHT_001",
                "file_path": "photos/RIGHT_001.jpg",
                "primary_face": "RIGHT",
                "original_filename": "02-original.jpg",
                "note": None,
            }
        ]


def test_original_p2_bytes_are_unchanged_and_no_other_photo_is_present() -> None:
    source = PHOTO.read_bytes()
    assert hashlib.sha256(source).hexdigest() == PHOTO_SHA256

    _, archive = _built_zip()
    with archive:
        packaged = archive.read("photos/RIGHT_001.jpg")
        assert packaged == source
        assert hashlib.sha256(packaged).hexdigest() == PHOTO_SHA256
        photo_entries = [name for name in archive.namelist() if name.startswith("photos/")]
        assert photo_entries == ["photos/RIGHT_001.jpg"]


def test_prompt_is_generic_and_contains_no_p2_answer_leak() -> None:
    prompt = PROMPT.read_text(encoding="utf-8")
    lowered = prompt.casefold()

    assert "boldungo.exchange.v1" in prompt
    assert "ANALYSIS_RESULT" in prompt
    assert "observations" in prompt
    assert "entités" in prompt
    assert "relations" in prompt
    assert "uncertainties" in prompt
    assert "question" in lowered
    assert "aucune représentation LEGO" in prompt

    for marker in FORBIDDEN_PACKAGE_MARKERS:
        assert marker.casefold() not in lowered


def test_evaluator_only_truth_is_separate_and_never_referenced_by_challenge() -> None:
    challenge_text = CHALLENGE.read_text(encoding="utf-8")
    challenge = json.loads(challenge_text)
    evaluator = json.loads(EVALUATOR.read_text(encoding="utf-8"))

    assert "evaluator" not in challenge_text.casefold()
    assert evaluator["benchmark_id"] == challenge["benchmark_id"]
    assert evaluator["photo_id"] == "RIGHT_001"
    assert evaluator["evaluator_only"] is True

    assert {item["classification"] for item in evaluator["visible_expected"]} == {
        "PHOTO_OBSERVABLE"
    }
    assert len(evaluator["visible_expected"]) >= 4
    assert {item["classification"] for item in evaluator["photo_insufficient"]} == {
        "PHOTO_INSUFFICIENT"
    }
    assert {item["classification"] for item in evaluator["forbidden_inference"]} == {
        "NON_PHOTO_FACT"
    }
    assert evaluator["evaluation_policy"]["keyword_only_matching_forbidden"] is True
    assert evaluator["evaluation_policy"]["justified_uncertainty_or_question_is_not_vision_failure"] is True

    builder_source = BUILDER.read_text(encoding="utf-8")
    assert "blind-p2-evaluator" not in builder_source
    assert "/evaluator/" not in builder_source


def test_blind_zip_has_no_ground_truth_or_house_specific_identifiers() -> None:
    _, archive = _built_zip()
    with archive:
        searchable = b"\n".join(
            name.encode("utf-8") + b"\n" + archive.read(name)
            for name in archive.namelist()
        ).decode("utf-8", errors="ignore").casefold()

    for marker in FORBIDDEN_PACKAGE_MARKERS:
        assert marker.casefold() not in searchable


def test_package_identity_supports_a_valid_v1_analysis_result() -> None:
    _, archive = _built_zip()
    with archive:
        manifest = json.loads(archive.read("manifest.json"))

    candidate_result = {
        "schema_version": "boldungo.exchange.v1",
        "message_type": "ANALYSIS_RESULT",
        "project_id": manifest["project_id"],
        "agent_id": manifest["agent_id"],
        "agent_display_name": manifest["agent_display_name"],
        "round_id": manifest["round_id"],
        "package_id": manifest["package_id"],
        "created_at": "2026-10-03T08:00:00Z",
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
    assert validate_exchange_v1(candidate_result) == {
        "status": "VALID ANALYSIS_RESULT",
        "reason": None,
    }


def test_blind_builder_has_no_network_or_ai_call() -> None:
    source = BUILDER.read_text(encoding="utf-8").casefold()
    for marker in ("fetch(", "requests.", "http://", "https://", "openai", "anthropic"):
        assert marker not in source
