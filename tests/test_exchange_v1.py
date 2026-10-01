import copy
import json
from pathlib import Path

from brickhouse.exchange_v1 import validate_exchange_v1


FIXTURES = Path(__file__).parent / "fixtures" / "exchange_v1"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_valid_analysis_result() -> None:
    result = validate_exchange_v1(_load("analysis_result_valid.json"))
    assert result == {"status": "VALID ANALYSIS_RESULT", "reason": None}


def test_valid_human_answers_against_source_result() -> None:
    result = validate_exchange_v1(
        _load("human_answers_valid.json"),
        source_analysis_result=_load("analysis_result_valid.json"),
    )
    assert result == {"status": "VALID HUMAN_ANSWERS", "reason": None}


def test_rejects_unknown_relation_type() -> None:
    payload = _load("analysis_result_valid.json")
    payload["payload"]["analysis"]["relations"][0]["relation_type"] = "NEAR"
    result = validate_exchange_v1(payload)
    assert result["status"] == "INVALID"
    assert "relation_type" in result["reason"]


def test_rejects_dangling_internal_observation_reference() -> None:
    payload = _load("analysis_result_valid.json")
    payload["payload"]["analysis"]["entities"][0]["observation_refs"] = ["O999"]
    result = validate_exchange_v1(payload)
    assert result["status"] == "INVALID"
    assert "unknown observations" in result["reason"]


def test_rejects_resolved_uncertainty_without_resolver() -> None:
    payload = _load("analysis_result_valid.json")
    uncertainty = payload["payload"]["analysis"]["uncertainties"][0]
    uncertainty["resolution_state"] = "RESOLVED"
    result = validate_exchange_v1(payload)
    assert result["status"] == "INVALID"
    assert "RESOLVED uncertainty requires" in result["reason"]


def test_rejects_question_with_unknown_uncertainty_ref() -> None:
    payload = _load("analysis_result_valid.json")
    payload["payload"]["questions"][0]["uncertainty_refs"] = ["U999"]
    result = validate_exchange_v1(payload)
    assert result["status"] == "INVALID"
    assert "unknown uncertainties" in result["reason"]


def test_rejects_unknown_answer_with_real_value() -> None:
    payload = _load("human_answers_valid.json")
    payload["payload"]["answers"][0]["answer_state"] = "UNKNOWN"
    result = validate_exchange_v1(payload)
    assert result["status"] == "INVALID"
    assert "UNKNOWN answer requires value=null" in result["reason"]


def test_rejects_invalid_yes_no_value_against_source_result() -> None:
    answers = _load("human_answers_valid.json")
    answers["payload"]["answers"][0]["value"] = "MAYBE"
    result = validate_exchange_v1(
        answers,
        source_analysis_result=_load("analysis_result_valid.json"),
    )
    assert result["status"] == "INVALID"
    assert "requires value YES or NO" in result["reason"]


def test_rejects_invalid_single_choice_value_against_source_result() -> None:
    answers = _load("human_answers_valid.json")
    answers["payload"]["answers"][1]["value"] = "STONE"
    result = validate_exchange_v1(
        answers,
        source_analysis_result=_load("analysis_result_valid.json"),
    )
    assert result["status"] == "INVALID"
    assert "requires one declared choice value" in result["reason"]


def test_rejects_unknown_when_question_disallows_it() -> None:
    source = _load("analysis_result_valid.json")
    source["payload"]["questions"][0]["allow_unknown"] = False
    answers = _load("human_answers_valid.json")
    answers["payload"]["answers"][0]["answer_state"] = "UNKNOWN"
    answers["payload"]["answers"][0]["value"] = None
    result = validate_exchange_v1(answers, source_analysis_result=source)
    assert result["status"] == "INVALID"
    assert "does not allow UNKNOWN" in result["reason"]


def test_rejects_extra_contract_field() -> None:
    payload = copy.deepcopy(_load("analysis_result_valid.json"))
    payload["payload"]["analysis"]["observations"][0]["confidence"] = 0.9
    result = validate_exchange_v1(payload)
    assert result["status"] == "INVALID"
    assert "Extra inputs are not permitted" in result["reason"]
