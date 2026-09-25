"""Canonical supplier-independent brick catalog models for M0."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class BrickDefinition(BaseModel):
    """A canonical standard brick expressed in integer grid units."""

    id: str
    category: Literal["brick", "plate"] = "brick"
    width_studs: int = Field(gt=0)
    length_studs: int = Field(gt=0)
    height_plates: int = Field(default=3, gt=0)
    connection_system: Literal["stud_tube"] = "stud_tube"

    @property
    def stud_count(self) -> int:
        return self.width_studs * self.length_studs

    @property
    def volume_grid_units(self) -> int:
        return self.width_studs * self.length_studs * self.height_plates

    def footprint(self, rotation_quarter_turns: int = 0) -> tuple[int, int]:
        """Return (width_studs, length_studs) after 90° grid rotations."""
        turns = rotation_quarter_turns % 4
        if turns % 2:
            return self.length_studs, self.width_studs
        return self.width_studs, self.length_studs


class BrickCatalog(BaseModel):
    schema_version: Literal["0.1"] = "0.1"
    catalog_id: str
    bricks: list[BrickDefinition] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_ids(self) -> "BrickCatalog":
        ids = [brick.id for brick in self.bricks]
        if len(ids) != len(set(ids)):
            raise ValueError("brick IDs must be unique")
        return self

    def get(self, brick_id: str) -> BrickDefinition:
        for brick in self.bricks:
            if brick.id == brick_id:
                return brick
        raise KeyError(brick_id)
