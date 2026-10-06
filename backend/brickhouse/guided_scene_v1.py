"""Minimal Guided House Package V1 -> ArchitecturalScene v0.2 bridge.

The guided package is the input boundary. Photo interpretation may be supplied by
an existing/external vision step as PHOTO/INFERRED candidates; USER_CONFIRMED
facts always win. This module deliberately does not import the blind Scene V2
benchmark prompts.
"""
from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import json
import re
from zipfile import ZipFile

from brickhouse.building import Appearance, AppearanceSection, Position3D, SourceInfo, SourceKind
from brickhouse.scene import ArchitecturalScene, Evidence, PropertyValue, SceneVolume

GUIDED_HOUSE_SCHEMA_VERSION = "boldungo.guided-house-package.v1"
PROVENANCE_LEVELS = ("USER_CONFIRMED", "PHOTO", "INFERRED", "UNKNOWN")


@dataclass(frozen=True)
class GuidedHouseInput:
    guided: dict
    photos: dict[str, bytes]


def parse_guided_house_package_v1(zip_bytes: bytes) -> GuidedHouseInput:
    if not isinstance(zip_bytes, (bytes, bytearray, memoryview)) or not zip_bytes:
        raise ValueError("Guided House Package V1 requires non-empty ZIP bytes")
    with ZipFile(BytesIO(bytes(zip_bytes)), "r") as archive:
        manifest = json.loads(archive.read("manifest.json"))
        if manifest.get("schema_version") != GUIDED_HOUSE_SCHEMA_VERSION:
            raise ValueError("unsupported guided package schema")
        guided_path = manifest.get("guided_data_path")
        if guided_path != "guided-house.json":
            raise ValueError("guided_data_path must be guided-house.json")
        guided = json.loads(archive.read(guided_path))
        if guided.get("schema_version") != GUIDED_HOUSE_SCHEMA_VERSION:
            raise ValueError("guided-house.json schema mismatch")
        photos = {}
        for item in manifest.get("photos", []):
            photo_id, file_path = item.get("photo_id"), item.get("file_path")
            if not photo_id or not file_path:
                raise ValueError("guided manifest photo requires photo_id and file_path")
            data = archive.read(file_path)
            if not data:
                raise ValueError(f"guided photo {photo_id} is empty")
            photos[photo_id] = data
        if not photos:
            raise ValueError("guided package requires at least one original photo")
        return GuidedHouseInput(guided=guided, photos=photos)


def _positive_number(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _known_dimension(guided: dict, pattern: str):
    rx = re.compile(pattern, re.IGNORECASE)
    for photo in guided.get("photos", []):
        if photo.get("provenance") != "USER_CONFIRMED":
            continue
        for text in photo.get("known_dimensions", []):
            match = rx.search(str(text).replace(",", "."))
            if match:
                return _positive_number(match.group(1))
    return None


def _candidate_value(candidates: dict | None, key: str):
    item = (candidates or {}).get(key)
    if not isinstance(item, dict):
        return None, "UNKNOWN", []
    provenance = item.get("provenance", "UNKNOWN")
    if provenance not in PROVENANCE_LEVELS:
        raise ValueError(f"unsupported provenance {provenance!r}")
    evidence = []
    for raw in item.get("evidence", []):
        if isinstance(raw, dict) and raw.get("photo_index") and raw.get("observation"):
            evidence.append(Evidence(photo_index=raw["photo_index"], observation=raw["observation"]))
    return _positive_number(item.get("value")), provenance, evidence


def _metric(guided: dict, candidates: dict | None, key: str, confirmed_value=None):
    if confirmed_value is not None:
        return PropertyValue(
            value=confirmed_value,
            source=SourceInfo(kind=SourceKind.USER_PROVIDED, confidence=1.0),
            evidence=[],
        )
    value, provenance, evidence = _candidate_value(candidates, key)
    source = {
        "PHOTO": SourceInfo(kind=SourceKind.OBSERVED, confidence=0.8),
        "INFERRED": SourceInfo(kind=SourceKind.INFERRED, confidence=0.5),
        "UNKNOWN": SourceInfo(kind=SourceKind.INFERRED, confidence=0.0),
        "USER_CONFIRMED": SourceInfo(kind=SourceKind.USER_PROVIDED, confidence=1.0),
    }[provenance]
    return PropertyValue(value=value, source=source, evidence=evidence)


def guided_house_to_architectural_scene(package: GuidedHouseInput, *, candidates: dict | None = None) -> ArchitecturalScene:
    """Build the smallest valid scene envelope without inventing missing metrics.

    `candidates` is the narrow adapter point for photo interpretation. It may carry
    PHOTO or INFERRED metric candidates; package USER_CONFIRMED dimensions override
    contradictory candidates. Missing values remain unknown (value=None).
    """
    guided = package.guided
    front_width = _positive_number(guided.get("known_front_width"))
    depth = _known_dimension(guided, r"(?:profondeur|depth)\s*(?:=|:)?\s*([0-9]+(?:\.[0-9]+)?)\s*m")
    height = _known_dimension(guided, r"(?:hauteur|height)\s*(?:=|:)?\s*([0-9]+(?:\.[0-9]+)?)\s*m")
    volume = SceneVolume(
        id="guided-main-volume",
        position=Position3D(x=0.0, y=0.0, z=0.0),
        width=_metric(guided, candidates, "front_width", front_width),
        depth=_metric(guided, candidates, "depth", depth),
        height=_metric(guided, candidates, "height", height),
        floors=1,
        source=SourceInfo(kind=SourceKind.USER_PROVIDED if front_width else SourceKind.INFERRED, confidence=1.0 if front_width else 0.0),
        evidence=[],
    )
    note = guided.get("general_notes") or None
    return ArchitecturalScene(
        schema_version="0.2",
        id=f"guided-{guided.get('project_id', 'house')}",
        name=f"Guided {guided.get('project_id', 'house')}",
        units="m",
        volumes=[volume],
        appearance=Appearance(walls=AppearanceSection(color="unknown")),
        notes=note,
    )


def reconstruct_guided_house_package_v1(zip_bytes: bytes, *, candidates: dict | None = None) -> ArchitecturalScene:
    return guided_house_to_architectural_scene(parse_guided_house_package_v1(zip_bytes), candidates=candidates)
