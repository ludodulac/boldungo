"""Verified canonical purchase-color mappings for supplier exports."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator


ColorMappingStatus = Literal["verified_catalog_identity"]


class ColorCrosswalkEntry(BaseModel):
    canonical_color_key: str = Field(min_length=1)
    bricklink_color_id: int = Field(gt=0)
    bricklink_name: str = Field(min_length=1)
    lego_color_name: str = Field(min_length=1)
    lego_color_id: int = Field(gt=0)
    mapping_status: ColorMappingStatus
    verification_source: str = Field(min_length=1)


class ColorCrosswalk(BaseModel):
    schema_version: Literal["0.1"] = "0.1"
    entries: list[ColorCrosswalkEntry]

    @model_validator(mode="after")
    def validate_unique_keys(self) -> "ColorCrosswalk":
        keys = [entry.canonical_color_key for entry in self.entries]
        if len(keys) != len(set(keys)):
            raise ValueError("color crosswalk canonical keys must be unique")
        return self

    def by_key(self) -> dict[str, ColorCrosswalkEntry]:
        return {entry.canonical_color_key: entry for entry in self.entries}


def default_color_crosswalk_path() -> Path:
    relative = Path("data") / "procurement" / "color_crosswalk.csv"
    candidates = (
        Path.cwd() / relative,
        Path(__file__).resolve().parents[3] / relative,
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    tried = ", ".join(str(candidate) for candidate in candidates)
    raise FileNotFoundError(f"procurement color crosswalk not found; tried: {tried}")


def load_color_crosswalk(path: str | Path | None = None) -> ColorCrosswalk:
    source = Path(path) if path is not None else default_color_crosswalk_path()
    with source.open("r", encoding="utf-8", newline="") as handle:
        entries = [ColorCrosswalkEntry(**row) for row in csv.DictReader(handle)]
    return ColorCrosswalk(entries=entries)
