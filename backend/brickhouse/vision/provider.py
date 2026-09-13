"""Explicit provider selection for BrickHouse photo analysis."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

from brickhouse.survey import ArchitecturalSurvey
from .gemini_provider import GeminiHTTPError, analyze_building_photos_gemini
from .models import PhotoAnalysisResult
from .openai_provider import PhotoInput, analyze_building_photos

VisionProviderName = Literal["openai", "gemini"]


class VisionProviderError(RuntimeError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class VisionStatus:
    ready: bool
    provider: VisionProviderName | None
    model: str | None
    reason: str


def configured_provider() -> str:
    return os.getenv("BRICKHOUSE_VISION_PROVIDER", "none").strip().lower() or "none"


def vision_status() -> VisionStatus:
    provider = configured_provider()
    if provider == "none":
        return VisionStatus(False, None, None, "provider_not_selected")
    if provider == "openai":
        if not os.getenv("OPENAI_API_KEY", "").strip():
            return VisionStatus(False, "openai", None, "missing_server_api_key")
        return VisionStatus(True, "openai", os.getenv("OPENAI_VISION_MODEL", "gpt-5").strip() or "gpt-5", "ready")
    if provider == "gemini":
        if not os.getenv("GEMINI_API_KEY", "").strip():
            return VisionStatus(False, "gemini", None, "missing_server_api_key")
        return VisionStatus(True, "gemini", os.getenv("GEMINI_VISION_MODEL", "gemini-3.6-flash").strip() or "gemini-3.6-flash", "ready")
    return VisionStatus(False, None, None, "unknown_provider")


def _gemini_error_code(status_code: int) -> str:
    if status_code == 400:
        return "gemini_request_rejected"
    if status_code in {401, 403}:
        return "gemini_auth_or_access"
    if status_code == 404:
        return "gemini_model_unavailable"
    if status_code == 429:
        return "gemini_quota_or_rate_limit"
    if status_code >= 500:
        return "gemini_upstream_unavailable"
    return "gemini_http_error"


def analyze_with_configured_provider(
    photos: list[PhotoInput], *, user_notes: str = "", known_front_width_m: float | None = None,
    survey: ArchitecturalSurvey | None = None,
) -> PhotoAnalysisResult:
    status = vision_status()
    if not status.ready or status.provider is None:
        raise VisionProviderError(status.reason)
    try:
        if status.provider == "openai":
            return analyze_building_photos(
                photos,
                user_notes=user_notes,
                known_front_width_m=known_front_width_m,
                survey=survey,
                model=status.model,
            )
        return analyze_building_photos_gemini(
            photos,
            user_notes=user_notes,
            known_front_width_m=known_front_width_m,
            survey=survey,
            model=status.model,
        )
    except ValueError:
        raise
    except GeminiHTTPError as exc:
        raise VisionProviderError(_gemini_error_code(exc.status_code)) from exc
    except Exception as exc:
        raise VisionProviderError("configured_provider_failed") from exc
