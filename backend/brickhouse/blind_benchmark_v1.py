"""Reproducible blind P2 benchmark adapter using the canonical V1 package builder.

This module is deliberately challenge-only. It reads exactly the blind challenge
configuration, generic prompt, and original P2 image. Evaluator files are not inputs.
"""
from __future__ import annotations

import json
from pathlib import Path

from .analysis_package_v1 import (
    AnalysisPackagePhoto,
    BuiltAnalysisPackage,
    build_analysis_package_v1,
)


_BENCHMARK_ROOT = (
    Path(__file__).resolve().parents[2]
    / "frontend"
    / "benchmarks"
    / "real-house-5"
)
_CHALLENGE_ROOT = _BENCHMARK_ROOT / "blind-p2"
_CHALLENGE_CONFIG = _CHALLENGE_ROOT / "challenge-input.json"
_MASTER_PROMPT_SOURCE = (
    Path(__file__).resolve().parents[2]
    / "frontend"
    / "analysis-prompt-v1-master.js"
)

_ALLOWED_TOP_LEVEL = {
    "schema_version",
    "benchmark_id",
    "project_id",
    "agent_id",
    "agent_display_name",
    "round_id",
    "photo",
    "prompt_path",
}
_ALLOWED_PHOTO_FIELDS = {
    "source_path",
    "photo_id",
    "primary_face",
    "original_filename",
    "note",
}


def _load_challenge() -> dict:
    document = json.loads(_CHALLENGE_CONFIG.read_text(encoding="utf-8"))
    if set(document) != _ALLOWED_TOP_LEVEL:
        raise ValueError("blind challenge config contains unsupported fields")
    if document["schema_version"] != "boldungo.blind-benchmark-challenge.v1":
        raise ValueError("unexpected blind challenge schema_version")
    if document["benchmark_id"] != "REAL-HOUSE-5-P2-BLIND":
        raise ValueError("unexpected blind benchmark_id")

    photo = document["photo"]
    if not isinstance(photo, dict) or set(photo) != _ALLOWED_PHOTO_FIELDS:
        raise ValueError("blind challenge photo descriptor contains unsupported fields")
    if photo["source_path"] != "../02-original.jpg":
        raise ValueError("blind P2 challenge must use only 02-original.jpg")
    if document["prompt_path"] != "prompt.txt":
        raise ValueError("blind P2 challenge must use its generic prompt.txt")
    return document


def _load_master_prompt_v1() -> str:
    source = _MASTER_PROMPT_SOURCE.read_text(encoding="utf-8")
    prefix = "export const MASTER_SOPHIE_PROMPT_V1 = `"
    suffix = "`;\n"
    if not source.startswith(prefix) or not source.endswith(suffix):
        raise ValueError("MASTER_SOPHIE_PROMPT_V1 must remain one static template literal export")
    prompt = source[len(prefix) : -len(suffix)]
    if "${" in prompt or "`" in prompt:
        raise ValueError("MASTER_SOPHIE_PROMPT_V1 must not contain interpolation or nested template literals")
    return prompt


def build_real_house_5_p2_blind_package(
    *,
    package_id: str,
    prompt_variant: str = "minimal",
) -> BuiltAnalysisPackage:
    """Build the exact Sophie R001 blind package without reading evaluator-only data."""
    challenge = _load_challenge()
    photo_spec = challenge["photo"]

    source_path = (_CHALLENGE_ROOT / photo_spec["source_path"]).resolve()
    expected_source = (_BENCHMARK_ROOT / "02-original.jpg").resolve()
    if source_path != expected_source:
        raise ValueError("blind challenge photo path escaped the approved P2 source")

    prompt_path = (_CHALLENGE_ROOT / challenge["prompt_path"]).resolve()
    if prompt_path.parent != _CHALLENGE_ROOT.resolve():
        raise ValueError("blind challenge prompt path escaped challenge input")

    photo_bytes = source_path.read_bytes()
    if prompt_variant == "minimal":
        prompt_text = prompt_path.read_text(encoding="utf-8")
    elif prompt_variant == "master":
        prompt_text = _load_master_prompt_v1()
    else:
        raise ValueError("prompt_variant must be 'minimal' or 'master'")

    return build_analysis_package_v1(
        project_id=challenge["project_id"],
        agent_id=challenge["agent_id"],
        agent_display_name=challenge["agent_display_name"],
        round_id=challenge["round_id"],
        package_id=package_id,
        photos=[
            AnalysisPackagePhoto(
                photo_id=photo_spec["photo_id"],
                primary_face=photo_spec["primary_face"],
                original_filename=photo_spec["original_filename"],
                data=photo_bytes,
                note=photo_spec["note"],
            )
        ],
        prompt_text=prompt_text,
    )
