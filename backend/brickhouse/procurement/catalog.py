"""Verified supplier-bridge catalog for procurement."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from brickhouse.bricks.piece_capabilities import PieceCapabilityRegistry


MappingStatus = Literal["verified_catalog_identity"]
EquivalencePolicy = Literal["bricklink_catalog_item", "exact_catalog_item"]


class PartCrosswalkEntry(BaseModel):
    engine_id: str = Field(min_length=1)
    bricklink_item_no: str | None = Field(default=None, min_length=1)
    ldraw_id: str | None = Field(default=None, min_length=1)
    rebrickable_part_num: str = Field(min_length=1)
    mapping_status: MappingStatus
    equivalence_policy: EquivalencePolicy
    verification_source: str = Field(min_length=1)
    ldraw_verification_source: str = Field(min_length=1)


class PartCrosswalk(BaseModel):
    schema_version: Literal["0.2"] = "0.2"
    entries: list[PartCrosswalkEntry]

    @model_validator(mode="after")
    def validate_unique_ids(self) -> "PartCrosswalk":
        ids = [entry.engine_id for entry in self.entries]
        if len(ids) != len(set(ids)):
            raise ValueError("part crosswalk engine IDs must be unique")
        return self

    def by_engine_id(self) -> dict[str, PartCrosswalkEntry]:
        return {entry.engine_id: entry for entry in self.entries}


class CrosswalkCoverage(BaseModel):
    approved_part_count: int = Field(ge=0)
    mapped_part_count: int = Field(ge=0)
    missing_engine_ids: list[str]
    extra_engine_ids: list[str]

    @property
    def complete(self) -> bool:
        return not self.missing_engine_ids


def default_part_crosswalk_path() -> Path:
    relative = Path("data") / "procurement" / "part_crosswalk.csv"
    candidates = (Path.cwd() / relative, Path(__file__).resolve().parents[3] / relative)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    tried = ", ".join(str(candidate) for candidate in candidates)
    raise FileNotFoundError(f"procurement part crosswalk not found; tried: {tried}")


def load_part_crosswalk(path: str | Path | None = None) -> PartCrosswalk:
    source = Path(path) if path is not None else default_part_crosswalk_path()
    with source.open("r", encoding="utf-8", newline="") as handle:
        entries = [PartCrosswalkEntry(**row) for row in csv.DictReader(handle)]
    return PartCrosswalk(entries=entries)


def audit_crosswalk_coverage(
    registry: PieceCapabilityRegistry,
    crosswalk: PartCrosswalk,
) -> CrosswalkCoverage:
    approved = registry.approved_ids()
    mapped = set(crosswalk.by_engine_id())
    return CrosswalkCoverage(
        approved_part_count=len(approved),
        mapped_part_count=len(approved & mapped),
        missing_engine_ids=sorted(approved - mapped),
        extra_engine_ids=sorted(mapped - approved),
    )


def require_complete_approved_crosswalk(
    registry: PieceCapabilityRegistry,
    crosswalk: PartCrosswalk,
) -> None:
    coverage = audit_crosswalk_coverage(registry, crosswalk)
    if coverage.missing_engine_ids:
        raise ValueError(
            "procurement crosswalk is missing placement-approved engine IDs: "
            + ", ".join(coverage.missing_engine_ids)
        )
