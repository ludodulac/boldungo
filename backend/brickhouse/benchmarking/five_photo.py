"""Isolation and diagnostic primitives for photo-only architecture benchmarks.

This module is benchmark infrastructure.  It deliberately does not import the
vision provider, Survey, Scene, or LEGO code: the candidate phase stages only
explicit source images, while the evaluator phase may load a private oracle
only after a candidate output has been frozen.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from enum import Enum
from pathlib import Path
from typing import Any


class Deductibility(str, Enum):
    OBSERVABLE_5 = "OBSERVABLE_5"
    MULTIVIEW_DEDUCIBLE_5 = "MULTIVIEW_DEDUCIBLE_5"
    HYPOTHESIS_ONLY_5 = "HYPOTHESIS_ONLY_5"
    UNKNOWN_FROM_5 = "UNKNOWN_FROM_5"


class PerceptualImportance(str, Enum):
    CRITICAL = "CRITICAL"
    IMPORTANT = "IMPORTANT"
    SECONDARY = "SECONDARY"


class Diagnostic(str, Enum):
    A = "A"  # correctly observed / identified
    B = "B"  # correctly related by multiview reasoning
    C = "C"  # reasonable hypothesis kept as hypothesis
    D = "D"  # honestly left unknown
    E = "E"  # perceptible element missed
    F = "F"  # wrong interpretation
    G = "G"  # hallucinated / invented certainty


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stage_candidate_inputs(
    *,
    source_dir: Path,
    candidate_dir: Path,
    expected_photos: list[dict[str, Any]],
) -> Path:
    """Create a fresh candidate workspace containing exactly the allowed images.

    The caller supplies the allow-list.  No benchmark oracle, owner fact,
    Scene, overlay, historical correction, test answer, or LEGO artifact is
    copied by this function.
    """
    if len(expected_photos) != 5:
        raise ValueError("nominal real-house benchmark requires exactly five photos")
    if candidate_dir.exists():
        shutil.rmtree(candidate_dir)
    images_dir = candidate_dir / "images"
    images_dir.mkdir(parents=True)

    staged: list[dict[str, Any]] = []
    for expected in expected_photos:
        index = int(expected["photo_index"])
        if index not in range(1, 6):
            raise ValueError(f"candidate photo index outside 1..5: {index}")
        filename = str(expected["path"])
        source = source_dir / filename
        actual_hash = sha256_file(source)
        if actual_hash != expected["sha256"]:
            raise ValueError(f"canonical photo hash mismatch: {filename}")
        destination = images_dir / filename
        shutil.copyfile(source, destination)
        staged.append(
            {
                "photo_index": index,
                "path": f"images/{filename}",
                "sha256": actual_hash,
            }
        )

    manifest = {
        "schema_version": "brickhouse-isolated-candidate-input-0.1",
        "benchmark_id": "real-house-5",
        "photos": staged,
    }
    manifest_path = candidate_dir / "candidate-input.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def freeze_candidate_output(candidate_dir: Path, payload: dict[str, Any]) -> Path:
    """Freeze the candidate result before any evaluator/oracle load."""
    path = candidate_dir / "candidate-output.json"
    if path.exists():
        raise FileExistsError("candidate output is already frozen")
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def load_oracle_after_candidate(*, candidate_output: Path, oracle_path: Path) -> dict[str, Any]:
    """Evaluator-only gate: the oracle cannot be loaded before candidate freeze."""
    if not candidate_output.is_file():
        raise RuntimeError("candidate output must be frozen before loading the oracle")
    return json.loads(oracle_path.read_text(encoding="utf-8"))


def classify_diagnostic(
    *,
    maximum_from_five: Deductibility,
    candidate_state: str,
    interpretation_correct: bool | None = None,
) -> Diagnostic:
    """Classify one truth without manufacturing a global score.

    candidate_state is intentionally small and representation-neutral:
    observed, multiview, hypothesis, unknown, missed, interpreted, certain.
    """
    if candidate_state == "unknown":
        return Diagnostic.D if maximum_from_five is Deductibility.UNKNOWN_FROM_5 else Diagnostic.E
    if candidate_state == "hypothesis":
        if maximum_from_five in {Deductibility.HYPOTHESIS_ONLY_5, Deductibility.UNKNOWN_FROM_5}:
            return Diagnostic.C
        return Diagnostic.E
    if candidate_state == "certain" and maximum_from_five in {
        Deductibility.HYPOTHESIS_ONLY_5,
        Deductibility.UNKNOWN_FROM_5,
    }:
        return Diagnostic.G
    if interpretation_correct is False:
        return Diagnostic.F
    if candidate_state == "multiview":
        return Diagnostic.B if interpretation_correct is not False else Diagnostic.F
    if candidate_state in {"observed", "interpreted", "certain"}:
        return Diagnostic.A if interpretation_correct is not False else Diagnostic.F
    if candidate_state == "missed":
        return Diagnostic.E
    raise ValueError(f"unsupported candidate_state: {candidate_state}")
