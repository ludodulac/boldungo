import json
from pathlib import Path

from fastapi.testclient import TestClient

import brickhouse.api as api_module
from brickhouse.api import app
from brickhouse.building.models import BuildingModel
from brickhouse.vision.models import ClarificationQuestion, PhotoAnalysisResult

client = TestClient(app)
REFERENCE = Path("docs/examples/building-model-simple-house.json")


def _reference_building() -> dict:
    return json.loads(REFERENCE.read_text(encoding="utf-8"))


def _analysis_result() -> PhotoAnalysisResult:
    building_data = _reference_building()
    building_data["metadata"]["created_from"] = "photo_analysis"
    return PhotoAnalysisResult(
        building=BuildingModel.model_validate(building_data),
        questions=[ClarificationQuestion(id="q1", question="Quelle est la largeur réelle de la façade ?", reason="Échelle absolue incertaine", importance="recommended")],
        assumptions=["L’arrière est supposé rectangulaire car il n’est pas visible."],
        confidence=0.74,
        needs_confirmation=True,
    )


def _enable_openai(monkeypatch):
    monkeypatch.setenv("BRICKHOUSE_VISION_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")


def test_health_endpoint(monkeypatch):
    monkeypatch.setenv("BRICKHOUSE_VISION_PROVIDER", "none")
    monkeypatch.delenv("RENDER_GIT_COMMIT", raising=False)
    payload = client.get("/health").json()
    assert payload == {
        "status": "ok", "service": "brickhouse-engine", "vision_enabled": False,
        "vision_provider": None, "vision_model": None,
        "vision_reason": "provider_not_selected", "engine_revision": "local",
    }


def test_health_reports_render_revision(monkeypatch):
    monkeypatch.setenv("BRICKHOUSE_VISION_PROVIDER", "none")
    monkeypatch.setenv("RENDER_GIT_COMMIT", "abc123")
    assert client.get("/health").json()["engine_revision"] == "abc123"


def test_health_reports_selected_openai(monkeypatch):
    _enable_openai(monkeypatch)
    monkeypatch.setenv("OPENAI_VISION_MODEL", "vision-test-model")
    payload = client.get("/health").json()
    assert payload["vision_enabled"] is True
    assert payload["vision_provider"] == "openai"
    assert payload["vision_model"] == "vision-test-model"


def test_capabilities_explain_provider_selection(monkeypatch):
    monkeypatch.setenv("BRICKHOUSE_VISION_PROVIDER", "none")
    monkeypatch.setenv("RENDER_GIT_COMMIT", "rev-1")
    payload = client.get("/api/v1/capabilities").json()
    assert payload["photo_analysis_ready"] is False
    assert payload["photo_provider"] is None
    assert payload["photo_model"] is None
    assert payload["photo_analysis_reason"] == "provider_not_selected"
    assert payload["engine_revision"] == "rev-1"
    assert payload["max_photos"] == 12

    monkeypatch.setenv("BRICKHOUSE_VISION_PROVIDER", "gemini")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    missing = client.get("/api/v1/capabilities").json()
    assert missing["photo_provider"] == "gemini"
    assert missing["photo_analysis_reason"] == "missing_server_api_key"

    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test-key")
    monkeypatch.setenv("GEMINI_VISION_MODEL", "gemini-test-model")
    enabled = client.get("/api/v1/capabilities").json()
    assert enabled["photo_analysis_ready"] is True
    assert enabled["photo_provider"] == "gemini"
    assert enabled["photo_model"] == "gemini-test-model"
    assert enabled["photo_analysis_reason"] == "ready"


def test_validate_external_ai_analysis_recomputes_compatibility():
    payload = _analysis_result().model_dump(mode="json")
    payload["m0_compatibility"] = {
        "buildable": False,
        "blockers": ["untrusted external value"],
        "warnings": [],
    }
    response = client.post("/api/v1/validate-analysis", json=payload)
    assert response.status_code == 200
    validated = response.json()
    assert validated["building"]["metadata"]["created_from"] == "photo_analysis"
    assert validated["m0_compatibility"]["buildable"] is True
    assert "untrusted external value" not in validated["m0_compatibility"]["blockers"]


def test_validate_external_ai_analysis_rejects_invalid_contract():
    payload = _analysis_result().model_dump(mode="json")
    payload["building"]["volumes"][0]["width"] = -10
    response = client.post("/api/v1/validate-analysis", json=payload)
    assert response.status_code == 422


def test_validated_external_ai_analysis_flows_into_build():
    payload = _analysis_result().model_dump(mode="json")
    validated = client.post("/api/v1/validate-analysis", json=payload)
    assert validated.status_code == 200
    built = client.post("/api/v1/build", json={"building": validated.json()["building"], "front_width_studs": 48})
    assert built.status_code == 200
    assert built.json()["bom"]["total_parts"] > 0


def test_build_endpoint_returns_canonical_export(monkeypatch):
    monkeypatch.setenv("RENDER_GIT_COMMIT", "test-revision")
    response = client.post("/api/v1/build", json={"building": _reference_building(), "front_width_studs": 48})
    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "0.1"
    assert payload["building_id"] == "building_simple_house_001"
    assert payload["metadata"]["engine_revision"] == "test-revision"
    assert payload["bom"]["total_parts"] == len(payload["brick_model"]["parts"])
    assert payload["assembly_plan"]["total_parts"] == payload["bom"]["total_parts"]


def test_build_endpoint_uses_default_front_width():
    response = client.post("/api/v1/build", json={"building": _reference_building()})
    assert response.status_code == 200
    assert response.json()["brick_model"]["width_studs"] == 48


def test_invalid_building_model_returns_422():
    broken = _reference_building(); broken["volumes"][0]["width"] = -1
    assert client.post("/api/v1/build", json={"building": broken}).status_code == 422


def test_invalid_target_width_returns_422():
    assert client.post("/api/v1/build", json={"building": _reference_building(), "front_width_studs": 0}).status_code == 422


def test_photo_analysis_is_disabled_without_selected_provider(monkeypatch):
    monkeypatch.setenv("BRICKHOUSE_VISION_PROVIDER", "none")
    response = client.post("/api/v1/analyze-photos", files=[("photos", ("front.jpg", b"fake", "image/jpeg"))])
    assert response.status_code == 503
    assert "provider_not_selected" in response.json()["detail"]


def test_photo_analysis_endpoint_returns_mocked_structured_result(monkeypatch):
    _enable_openai(monkeypatch)
    captured = {}
    def fake_analyze(photos, *, user_notes="", known_front_width_m=None, survey=None):
        captured.update(count=len(photos), notes=user_notes, width=known_front_width_m, survey=survey)
        return _analysis_result()
    monkeypatch.setattr(api_module, "analyze_with_configured_provider", fake_analyze)
    response = client.post(
        "/api/v1/analyze-photos",
        files=[("photos", ("front.jpg", b"front", "image/jpeg")), ("photos", ("side.png", b"side", "image/png"))],
        data={"user_notes": "Terrasse à gauche", "known_front_width_m": "10.2"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["building"]["metadata"]["created_from"] == "photo_analysis"
    assert payload["needs_confirmation"] is True
    assert captured == {"count": 2, "notes": "Terrasse à gauche", "width": 10.2, "survey": None}


def test_photo_proposal_can_flow_directly_into_brick_build(monkeypatch):
    _enable_openai(monkeypatch)
    monkeypatch.setenv("RENDER_GIT_COMMIT", "photo-mvp")
    monkeypatch.setattr(api_module, "analyze_with_configured_provider", lambda *args, **kwargs: _analysis_result())
    analyzed = client.post("/api/v1/analyze-photos", files=[("photos", ("front.jpg", b"front", "image/jpeg"))], data={"known_front_width_m": "10.0"})
    assert analyzed.status_code == 200
    proposal = analyzed.json()["building"]
    built = client.post("/api/v1/build", json={"building": proposal, "front_width_studs": 48})
    assert built.status_code == 200
    export = built.json()
    assert export["building_id"] == proposal["id"]
    assert export["metadata"]["engine_revision"] == "photo-mvp"
    assert export["bom"]["total_parts"] == len(export["brick_model"]["parts"])
    assert export["assembly_plan"]["total_steps"] > 0


def test_photo_analysis_rejects_unsupported_file_type(monkeypatch):
    _enable_openai(monkeypatch)
    response = client.post("/api/v1/analyze-photos", files=[("photos", ("plan.pdf", b"pdf", "application/pdf"))])
    assert response.status_code == 415


def test_photo_analysis_accepts_richer_multi_view_set(monkeypatch):
    _enable_openai(monkeypatch)
    monkeypatch.setattr(api_module, "analyze_with_configured_provider", lambda *args, **kwargs: _analysis_result())
    files = [("photos", (f"p{i}.jpg", b"photo", "image/jpeg")) for i in range(12)]
    assert client.post("/api/v1/analyze-photos", files=files).status_code == 200


def test_photo_analysis_rejects_too_many_photos(monkeypatch):
    _enable_openai(monkeypatch)
    files = [("photos", (f"p{i}.jpg", b"photo", "image/jpeg")) for i in range(13)]
    assert client.post("/api/v1/analyze-photos", files=files).status_code == 422
