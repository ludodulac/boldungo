"""Canonical order-package models.

These models deliberately stop before supplier resolution. They conserve every
BrickModel placement and BagPlan assignment so later exporters can translate the
same package to LEGO, BrickLink, GoBricks, or another supplier without changing
construction geometry or bag boundaries.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from brickhouse.bricks.brick_model import PartCategory


class OrderLine(BaseModel):
    part_id: str = Field(min_length=1)
    category: PartCategory
    semantic_color: str | None = Field(default=None, min_length=1)
    quantity: int = Field(gt=0)


class BagOrderManifest(BaseModel):
    bag_number: int = Field(gt=0)
    phases: list[str] = Field(min_length=1)
    assembly_step_ids: list[str] = Field(min_length=1)
    total_parts: int = Field(gt=0)
    lines: list[OrderLine] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_total(self) -> "BagOrderManifest":
        if self.total_parts != sum(line.quantity for line in self.lines):
            raise ValueError("bag total_parts does not match line quantities")
        return self


class CanonicalOrderPackage(BaseModel):
    """Exact supplier-independent procurement package for one built volume."""

    schema_version: Literal["0.1"] = "0.1"
    building_id: str
    volume_id: str
    supplier_state: Literal["canonical_only"] = "canonical_only"
    total_parts: int = Field(gt=0)
    unique_part_types: int = Field(gt=0)
    total_bags: int = Field(gt=0)
    order_lines: list[OrderLine] = Field(min_length=1)
    bags: list[BagOrderManifest] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_conservation(self) -> "CanonicalOrderPackage":
        if self.total_parts != sum(line.quantity for line in self.order_lines):
            raise ValueError("order package total_parts does not match order line quantities")
        if self.unique_part_types != len(self.order_lines):
            raise ValueError("unique_part_types does not match order_lines length")
        if [bag.bag_number for bag in self.bags] != list(range(1, self.total_bags + 1)):
            raise ValueError("bag numbers must be contiguous from 1")
        if self.total_parts != sum(bag.total_parts for bag in self.bags):
            raise ValueError("order package total_parts does not match bag totals")
        return self
