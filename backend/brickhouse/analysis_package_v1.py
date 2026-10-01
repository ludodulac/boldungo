"""Build in-memory BOLDÜNGO V1 analysis ZIP packages."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
import json
from pathlib import PurePath
import re
from typing import Iterable
from zipfile import ZIP_STORED, ZipFile

from .exchange_v1 import _validate_package_id


MANIFEST_SCHEMA_VERSION = "boldungo.analysis-package-manifest.v1"
_PRIMARY_FACES = {"FRONT", "RIGHT", "LEFT", "REAR"}
_TECHNICAL_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
_ROUND_ID_RE = re.compile(r"^R\d{3,}$")
_PHOTO_ID_RE = re.compile(r"^(FRONT|RIGHT|LEFT|REAR)_\d{3,}$")
_EXTENSION_RE = re.compile(r"^\.[A-Za-z0-9]+$")


@dataclass(frozen=True)
class AnalysisPackagePhoto:
    photo_id: str
    primary_face: str
    original_filename: str
    data: bytes
    note: str | None = None


@dataclass(frozen=True)
class BuiltAnalysisPackage:
    filename: str
    zip_bytes: bytes


def _require_nonempty(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _validate_technical_id(value: str, label: str) -> str:
    value = _require_nonempty(value, label)
    if not _TECHNICAL_ID_RE.fullmatch(value):
        raise ValueError(f"{label} must contain only ASCII letters, digits, underscore or hyphen")
    return value


def _original_extension(filename: str) -> str:
    filename = _require_nonempty(filename, "original_filename")
    suffix = PurePath(filename).suffix
    if not suffix or not _EXTENSION_RE.fullmatch(suffix):
        raise ValueError(f"cannot determine a safe original extension from {filename!r}")
    return suffix


def _manifest_created_at() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def build_analysis_package_v1(
    *,
    project_id: str,
    agent_id: str,
    agent_display_name: str,
    round_id: str,
    package_id: str,
    photos: Iterable[AnalysisPackagePhoto],
    prompt_text: str,
) -> BuiltAnalysisPackage:
    """Build the exact minimal V1 analysis package entirely in memory."""

    project_id = _validate_technical_id(project_id, "project_id")
    agent_id = _validate_technical_id(agent_id, "agent_id")
    _require_nonempty(agent_display_name, "agent_display_name")
    if not isinstance(round_id, str) or not _ROUND_ID_RE.fullmatch(round_id):
        raise ValueError("round_id must use R001, R002, ...")
    _validate_package_id(package_id)
    if not isinstance(prompt_text, str):
        raise ValueError("prompt_text must be a string")

    photo_list = list(photos)
    if not photo_list:
        raise ValueError("analysis package requires at least one photo")

    photo_ids: set[str] = set()
    file_paths: set[str] = set()
    prepared: list[tuple[AnalysisPackagePhoto, str, bytes]] = []
    manifest_photos: list[dict[str, str | None]] = []

    for photo in photo_list:
        if not isinstance(photo, AnalysisPackagePhoto):
            raise ValueError("photos must contain AnalysisPackagePhoto entries")
        if not _PHOTO_ID_RE.fullmatch(photo.photo_id):
            raise ValueError(f"invalid photo_id {photo.photo_id!r}")
        if photo.photo_id in photo_ids:
            raise ValueError(f"duplicate photo_id {photo.photo_id}")
        photo_ids.add(photo.photo_id)

        if photo.primary_face not in _PRIMARY_FACES:
            raise ValueError(f"invalid primary_face {photo.primary_face!r}")
        if not photo.photo_id.startswith(f"{photo.primary_face}_"):
            raise ValueError(
                f"photo_id {photo.photo_id} does not match primary_face {photo.primary_face}"
            )

        extension = _original_extension(photo.original_filename)
        file_path = f"photos/{photo.photo_id}{extension}"
        if file_path in file_paths:
            raise ValueError(f"duplicate final file_path {file_path}")
        file_paths.add(file_path)

        if not isinstance(photo.data, (bytes, bytearray, memoryview)) or not photo.data:
            raise ValueError(f"photo {photo.photo_id} requires non-empty binary data")
        data = bytes(photo.data)

        if photo.note is not None and not isinstance(photo.note, str):
            raise ValueError(f"photo {photo.photo_id} note must be a string or null")

        prepared.append((photo, file_path, data))
        manifest_photos.append(
            {
                "photo_id": photo.photo_id,
                "file_path": file_path,
                "primary_face": photo.primary_face,
                "original_filename": photo.original_filename,
                "note": photo.note,
            }
        )

    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "project_id": project_id,
        "agent_id": agent_id,
        "agent_display_name": agent_display_name,
        "round_id": round_id,
        "package_id": package_id,
        "created_at": _manifest_created_at(),
        "prompt_path": "prompt.txt",
        "photos": manifest_photos,
    }

    buffer = BytesIO()
    with ZipFile(buffer, mode="w", compression=ZIP_STORED) as archive:
        archive.writestr(
            "manifest.json",
            (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
        )
        archive.writestr("prompt.txt", prompt_text.encode("utf-8"))
        for _, file_path, data in prepared:
            archive.writestr(file_path, data)

    filename = f"BOLDUNGO_{project_id}_{agent_id}_{round_id}.zip"
    return BuiltAnalysisPackage(filename=filename, zip_bytes=buffer.getvalue())
