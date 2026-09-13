"""Gemini generateContent provider using the shared BrickHouse vision contract."""
from __future__ import annotations

import base64
import json
import os
from typing import Any

import httpx
from pydantic import ValidationError

from brickhouse.survey import ArchitecturalSurvey
from .models import PhotoAnalysisResult
from .openai_provider import MAX_VISION_PHOTOS, PhotoInput, SYSTEM_PROMPT, _survey_context

MAX_GEMINI_INLINE_RAW_BYTES = 14 * 1024 * 1024


class GeminiHTTPError(RuntimeError):
    def __init__(self, status_code: int):
        super().__init__(f"Gemini HTTP {status_code}")
        self.status_code = status_code


def _prompt(
    user_notes: str,
    known_front_width_m: float | None,
    photo_count: int,
    survey: ArchitecturalSurvey | None,
) -> str:
    return (
        "Analyze these photos as overlapping views of the same physical property. "
        f"There are {photo_count} supplied views. Do not use photo count itself as certainty: identify repeated physical objects, wall planes and corner crossings before estimating geometry. "
        f"User notes: {user_notes.strip() or 'none provided'}. "
        f"Known front width in meters: {known_front_width_m if known_front_width_m is not None else 'unknown'}. "
        f"{_survey_context(survey)} "
        "Lock the observed opening inventory per physical wall before metric placement. "
        "Use extra/detail views to refine only the relations they actually reveal. Hidden stair, landing or terrace connections must remain uncertain rather than being completed by architectural habit. "
        "Recover normalized proportions before metric dimensions and cross-check them across compatible views. "
        "Also return a bounded set of normally 8–15 high-value architectural landmark_proposals. Reuse a physical_landmark_id across views only when physical identity is defensible; resemblance alone is insufficient. "
        "Coordinates are x/width and y/height proposals, not calibrated camera coordinates. Mark ambiguous or rejected identities explicitly rather than manufacturing enough points. "
        "When the read-only Survey identifies the object but omits a supplied photo where it is directly visible, return a survey_evidence_candidate instead of pretending that evidence is already accepted. "
        "Return the most faithful conservative proposal allowed by the BuildingModel schema, plus questions, assumptions, scale_basis, proportion_evidence, landmark_proposals and survey_evidence_candidates. "
        "Never change an observed architectural feature merely to make the proposal compatible with the current LEGO engine."
    )


def _extract_text(payload: dict[str, Any]) -> str:
    candidates = payload.get("candidates") or []
    if not candidates:
        raise ValueError("vision provider returned no candidate")
    parts = ((candidates[0].get("content") or {}).get("parts") or [])
    text = "".join(str(part.get("text", "")) for part in parts if part.get("text"))
    if not text:
        raise ValueError("vision provider returned no structured output")
    return text.strip()


def _clean_json_text(text: str) -> str:
    value = text.strip()
    if value.startswith("```"):
        lines = value.splitlines()
        if lines and lines[0].strip().lower() in {"```", "```json"}:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        value = "\n".join(lines).strip()
    return value


def _validate_result(text: str) -> PhotoAnalysisResult:
    return PhotoAnalysisResult.model_validate_json(_clean_json_text(text))


def _repair_prompt(invalid_text: str, exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        errors = exc.errors(include_url=False, include_context=False)
    else:
        errors = [{"error": str(exc)}]
    return (
        "Repair the following BrickHouse photo-analysis candidate so it validates exactly against the supplied JSON schema. "
        "Preserve all architectural observations, landmark identities, evidence candidates, dimensions and uncertainty unless a value itself violates a schema or cross-field constraint. "
        "Do not invent missing observations or landmarks merely to make validation pass. Return JSON only.\n\n"
        f"VALIDATION ERRORS:\n{json.dumps(errors, ensure_ascii=False)}\n\n"
        f"CANDIDATE:\n{invalid_text}"
    )


def _post_json(http: httpx.Client, url: str, key: str, body: dict[str, Any]) -> str:
    response = http.post(url, headers={"x-goog-api-key": key, "Content-Type": "application/json"}, json=body)
    if not response.is_success:
        raise GeminiHTTPError(response.status_code)
    return _extract_text(response.json())


def analyze_building_photos_gemini(
    photos: list[PhotoInput], *, user_notes: str = "", known_front_width_m: float | None = None,
    survey: ArchitecturalSurvey | None = None,
    client: httpx.Client | None = None, model: str | None = None, api_key: str | None = None,
) -> PhotoAnalysisResult:
    if not 1 <= len(photos) <= MAX_VISION_PHOTOS:
        raise ValueError(f"photo analysis requires between 1 and {MAX_VISION_PHOTOS} images")
    if known_front_width_m is not None and known_front_width_m <= 0:
        raise ValueError("known_front_width_m must be positive")
    supported = {"image/jpeg", "image/png", "image/webp"}
    for photo in photos:
        if photo.media_type not in supported:
            raise ValueError(f"unsupported image type: {photo.media_type}")
        if not photo.content:
            raise ValueError(f"empty image: {photo.filename}")
    if sum(len(photo.content) for photo in photos) > MAX_GEMINI_INLINE_RAW_BYTES:
        raise ValueError("Pour le fournisseur Gemini, réduisez la taille totale des photos sous 14 Mo pour cet essai.")

    selected_model = model or os.getenv("GEMINI_VISION_MODEL", "gemini-3.6-flash")
    key = api_key or os.getenv("GEMINI_API_KEY", "")
    if not key.strip():
        raise ValueError("Gemini API key is not configured")

    parts = [{"inline_data": {"mime_type": p.media_type, "data": base64.b64encode(p.content).decode("ascii")}} for p in photos]
    parts.append({"text": _prompt(user_notes, known_front_width_m, len(photos), survey)})
    schema = PhotoAnalysisResult.model_json_schema()
    generation = {"responseMimeType": "application/json", "responseJsonSchema": schema}
    body = {"system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]}, "contents": [{"role": "user", "parts": parts}], "generationConfig": generation}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{selected_model}:generateContent"
    owns_client = client is None
    http = client or httpx.Client(timeout=90.0)
    try:
        text = _post_json(http, url, key, body)
        try:
            return _validate_result(text)
        except (json.JSONDecodeError, ValidationError, ValueError) as first_error:
            repair_body = {"system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]}, "contents": [{"role": "user", "parts": [{"text": _repair_prompt(text, first_error)}]}], "generationConfig": generation}
            repaired = _post_json(http, url, key, repair_body)
            try:
                return _validate_result(repaired)
            except (json.JSONDecodeError, ValidationError, ValueError) as exc:
                raise ValueError("vision provider returned invalid structured output after repair") from exc
    finally:
        if owns_client:
            http.close()
